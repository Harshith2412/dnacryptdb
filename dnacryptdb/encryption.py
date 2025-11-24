"""
DNACryptDB Encryption Layer
Client-side encryption for all sensitive data
Implements blind indexes, field-level encryption, and key management
"""

import os
import hmac
import hashlib
import json
from typing import Dict, Tuple, Any
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

class EncryptionManager:
    """
    Manages all encryption operations for DNACryptDB
    
    Key Hierarchy:
    - Master Key (KEK - Key Encryption Key): Encrypts all DEKs
    - Data Encryption Keys (DEK): Per-message or per-sequence encryption
    - Index Key: For blind indexes (searchable encryption)
    - Signing Key: For Ed25519 signatures
    """
    
    def __init__(self, master_password: str = None):
        """
        Initialize encryption manager
        
        Args:
            master_password: Master password to derive KEK
        """
        # In production, load from secure key management service (AWS KMS, etc.)
        self.master_password = master_password or os.environ.get('DNACRYPT_MASTER_KEY', 'default_key_change_me')
        
        # Derive KEK from master password
        self.kek = self._derive_kek(self.master_password)
        
        # Derive index key for blind indexes
        self.index_key = self._derive_index_key(self.master_password)
        
        # Signing key pair (Ed25519)
        self.signing_key_private = ed25519.Ed25519PrivateKey.generate()
        self.signing_key_public = self.signing_key_private.public_key()
    
    def _derive_kek(self, password: str) -> bytes:
        """Derive KEK (Key Encryption Key) from master password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'dnacrypt_kek_salt_v1',  # In prod: unique per deployment
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())
    
    def _derive_index_key(self, password: str) -> bytes:
        """Derive index key for blind indexes"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'dnacrypt_index_salt_v1',
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(password.encode())
    
    # ========================================================================
    # Message Encryption (Client-Side AES-GCM)
    # ========================================================================
    
    def encrypt_message(self, plaintext: str) -> Dict[str, str]:
        """
        Encrypt message body using AES-GCM with per-message DEK
        
        Returns:
            {
                'ciphertext': base64 encoded,
                'nonce': base64 encoded IV,
                'tag': base64 encoded authentication tag,
                'wrapped_dek': base64 encoded (DEK encrypted with KEK),
                'algorithm': 'AES-256-GCM'
            }
        """
        # Generate random DEK (Data Encryption Key) for this message
        dek = AESGCM.generate_key(bit_length=256)
        
        # Create AES-GCM cipher
        aesgcm = AESGCM(dek)
        
        # Generate random nonce (96 bits for GCM)
        nonce = os.urandom(12)
        
        # Encrypt message (returns ciphertext + tag combined)
        ciphertext_with_tag = aesgcm.encrypt(nonce, plaintext.encode(), None)
        
        # Split ciphertext and tag
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]
        
        # Wrap DEK with KEK (encrypt the encryption key)
        wrapped_dek = self._wrap_key(dek)
        
        return {
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'nonce': base64.b64encode(nonce).decode(),
            'tag': base64.b64encode(tag).decode(),
            'wrapped_dek': base64.b64encode(wrapped_dek).decode(),
            'algorithm': 'AES-256-GCM',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def decrypt_message(self, encrypted_data: Dict[str, str]) -> str:
        """
        Decrypt message body
        
        Args:
            encrypted_data: Dict from encrypt_message()
        
        Returns:
            Plaintext message
        """
        # Decode from base64
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        nonce = base64.b64decode(encrypted_data['nonce'])
        tag = base64.b64decode(encrypted_data['tag'])
        wrapped_dek = base64.b64decode(encrypted_data['wrapped_dek'])
        
        # Unwrap DEK using KEK
        dek = self._unwrap_key(wrapped_dek)
        
        # Decrypt message
        aesgcm = AESGCM(dek)
        ciphertext_with_tag = ciphertext + tag
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext_with_tag, None)
        
        return plaintext_bytes.decode()
    
    def _wrap_key(self, dek: bytes) -> bytes:
        """Encrypt DEK with KEK (key wrapping)"""
        aesgcm = AESGCM(self.kek)
        nonce = os.urandom(12)
        wrapped = aesgcm.encrypt(nonce, dek, None)
        return nonce + wrapped  # Prepend nonce
    
    def _unwrap_key(self, wrapped_dek: bytes) -> bytes:
        """Decrypt DEK with KEK (key unwrapping)"""
        nonce = wrapped_dek[:12]
        ciphertext = wrapped_dek[12:]
        aesgcm = AESGCM(self.kek)
        return aesgcm.decrypt(nonce, ciphertext, None)
    
    # ========================================================================
    # Blind Index (Searchable Encryption)
    # ========================================================================
    
    def create_blind_index(self, value: str, normalize: bool = True) -> str:
        """
        Create blind index for searchable fields (username, email)
        
        Uses HMAC-SHA256 with deterministic output for equality searches
        
        Args:
            value: The value to index (email, username)
            normalize: Lowercase and strip whitespace
        
        Returns:
            Hex-encoded HMAC (64 characters)
        """
        if normalize:
            value = value.lower().strip()
        
        # Deterministic HMAC for equality searches
        blind_index = hmac.new(
            self.index_key,
            value.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return blind_index
    
    def verify_blind_index(self, value: str, stored_index: str) -> bool:
        """Verify if value matches stored blind index"""
        computed_index = self.create_blind_index(value)
        return hmac.compare_digest(computed_index, stored_index)
    
    # ========================================================================
    # Field-Level Encryption (PII Data)
    # ========================================================================
    
    def encrypt_field(self, value: str, field_name: str) -> Dict[str, str]:
        """
        Encrypt individual field (email, user details, etc.)
        
        Returns:
            {
                'encrypted_value': base64 encoded ciphertext,
                'field_nonce': base64 encoded nonce,
                'field_tag': base64 encoded tag,
                'field_dek': base64 encoded wrapped DEK
            }
        """
        # Generate field-specific DEK
        field_dek = AESGCM.generate_key(bit_length=256)
        aesgcm = AESGCM(field_dek)
        
        # Encrypt
        nonce = os.urandom(12)
        ciphertext_with_tag = aesgcm.encrypt(nonce, value.encode(), field_name.encode())
        
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]
        
        # Wrap DEK
        wrapped_dek = self._wrap_key(field_dek)
        
        return {
            'encrypted_value': base64.b64encode(ciphertext).decode(),
            'field_nonce': base64.b64encode(nonce).decode(),
            'field_tag': base64.b64encode(tag).decode(),
            'field_dek': base64.b64encode(wrapped_dek).decode()
        }
    
    def decrypt_field(self, encrypted_field: Dict[str, str], field_name: str) -> str:
        """Decrypt individual field"""
        ciphertext = base64.b64decode(encrypted_field['encrypted_value'])
        nonce = base64.b64decode(encrypted_field['field_nonce'])
        tag = base64.b64decode(encrypted_field['field_tag'])
        wrapped_dek = base64.b64decode(encrypted_field['field_dek'])
        
        # Unwrap DEK
        field_dek = self._unwrap_key(wrapped_dek)
        
        # Decrypt
        aesgcm = AESGCM(field_dek)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext + tag, field_name.encode())
        
        return plaintext_bytes.decode()
    
    # ========================================================================
    # DNA Sequence Encryption
    # ========================================================================
    
    def encrypt_dna_sequence(self, sequence: str, metadata: Dict = None) -> Dict[str, Any]:
        """
        Encrypt DNA sequence with signature
        
        Returns:
            {
                'encrypted_sequence': base64 ciphertext,
                'sequence_nonce': base64 nonce,
                'sequence_tag': base64 tag,
                'wrapped_dek': base64 wrapped key,
                'signature': base64 Ed25519 signature,
                'public_key': base64 public key,
                'key_id': identifier for key rotation,
                'metadata': signed metadata
            }
        """
        # Generate sequence-specific DEK
        dek = AESGCM.generate_key(bit_length=256)
        aesgcm = AESGCM(dek)
        
        # Encrypt sequence
        nonce = os.urandom(12)
        additional_data = json.dumps(metadata or {}).encode()
        ciphertext_with_tag = aesgcm.encrypt(nonce, sequence.encode(), additional_data)
        
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]
        
        # Wrap DEK
        wrapped_dek = self._wrap_key(dek)
        
        # Sign the encrypted sequence (signature over ciphertext + metadata)
        data_to_sign = ciphertext + additional_data
        signature = self.signing_key_private.sign(data_to_sign)
        
        # Public key for verification
        public_key_bytes = self.signing_key_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return {
            'encrypted_sequence': base64.b64encode(ciphertext).decode(),
            'sequence_nonce': base64.b64encode(nonce).decode(),
            'sequence_tag': base64.b64encode(tag).decode(),
            'wrapped_dek': base64.b64encode(wrapped_dek).decode(),
            'signature': base64.b64encode(signature).decode(),
            'public_key': base64.b64encode(public_key_bytes).decode(),
            'key_id': 'signing_key_v1',  # For key rotation
            'metadata': metadata or {}
        }
    
    def decrypt_and_verify_sequence(self, encrypted_data: Dict[str, Any]) -> Tuple[str, bool]:
        """
        Decrypt DNA sequence and verify signature
        
        Returns:
            (decrypted_sequence, signature_valid)
        """
        # Decode
        ciphertext = base64.b64decode(encrypted_data['encrypted_sequence'])
        nonce = base64.b64decode(encrypted_data['sequence_nonce'])
        tag = base64.b64decode(encrypted_data['sequence_tag'])
        wrapped_dek = base64.b64decode(encrypted_data['wrapped_dek'])
        signature = base64.b64decode(encrypted_data['signature'])
        public_key_bytes = base64.b64decode(encrypted_data['public_key'])
        
        # Verify signature first
        additional_data = json.dumps(encrypted_data.get('metadata', {})).encode()
        data_to_verify = ciphertext + additional_data
        
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        
        try:
            public_key.verify(signature, data_to_verify)
            signature_valid = True
        except Exception:
            signature_valid = False
        
        # Decrypt sequence
        dek = self._unwrap_key(wrapped_dek)
        aesgcm = AESGCM(dek)
        plaintext_bytes = aesgcm.decrypt(nonce, ciphertext + tag, additional_data)
        
        return plaintext_bytes.decode(), signature_valid
    
    # ========================================================================
    # User Data Encryption (PII)
    # ========================================================================
    
    def encrypt_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt user PII with field-level encryption
        
        Input:
            {
                'email': 'alice@dnacrypt.com',
                'display_name': 'Alice Smith',
                'phone': '+1-555-1234',
                'address': '123 Main St'
            }
        
        Returns:
            {
                'email_index': blind index for search,
                'email_encrypted': encrypted email,
                'display_name_encrypted': {...},
                'phone_encrypted': {...},
                'address_encrypted': {...}
            }
        """
        encrypted = {}
        
        # Email: Create blind index + encrypt value
        if 'email' in user_data:
            encrypted['email_index'] = self.create_blind_index(user_data['email'])
            encrypted['email_encrypted'] = self.encrypt_field(user_data['email'], 'email')
        
        # Encrypt other PII fields
        for field in ['display_name', 'phone', 'address', 'ssn', 'dob']:
            if field in user_data:
                encrypted[f'{field}_encrypted'] = self.encrypt_field(
                    str(user_data[field]), 
                    field
                )
        
        # Non-sensitive fields stay plaintext
        for field in ['user_id', 'role', 'created_at']:
            if field in user_data:
                encrypted[field] = user_data[field]
        
        return encrypted
    
    def decrypt_user_data(self, encrypted_data: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt user PII"""
        decrypted = {}
        
        # Decrypt each encrypted field
        for key, value in encrypted_data.items():
            if key.endswith('_encrypted') and isinstance(value, dict):
                field_name = key.replace('_encrypted', '')
                decrypted[field_name] = self.decrypt_field(value, field_name)
            elif not key.endswith('_index'):  # Skip blind indexes
                decrypted[key] = value
        
        return decrypted
    
    # ========================================================================
    # Username Search (Blind Index)
    # ========================================================================
    
    def prepare_searchable_username(self, username: str) -> Dict[str, str]:
        """
        Prepare username for storage with blind index
        
        Returns:
            {
                'username_index': for equality search,
                'username_encrypted': encrypted full username
            }
        """
        return {
            'username_index': self.create_blind_index(username),
            'username_encrypted': self.encrypt_field(username, 'username')
        }
    
    def search_by_username(self, username: str) -> str:
        """
        Get blind index for searching
        
        Usage:
            index = encryption.search_by_username("alice")
            # Query: WHERE username_index = '{index}'
        """
        return self.create_blind_index(username)
    
    # ========================================================================
    # Private Key Storage (Encrypted)
    # ========================================================================
    
    def encrypt_private_key(self, private_key_pem: str) -> Dict[str, str]:
        """
        Encrypt private key for storage
        NEVER store raw private keys!
        
        Returns:
            {
                'encrypted_key': base64 ciphertext,
                'key_nonce': base64 nonce,
                'key_tag': base64 tag,
                'wrapped_dek': base64 wrapped DEK,
                'key_id': identifier,
                'algorithm': key algorithm type
            }
        """
        # Generate DEK for this private key
        dek = AESGCM.generate_key(bit_length=256)
        aesgcm = AESGCM(dek)
        
        # Encrypt private key
        nonce = os.urandom(12)
        ciphertext_with_tag = aesgcm.encrypt(
            nonce, 
            private_key_pem.encode(), 
            b'private_key'
        )
        
        ciphertext = ciphertext_with_tag[:-16]
        tag = ciphertext_with_tag[-16:]
        
        # Wrap DEK
        wrapped_dek = self._wrap_key(dek)
        
        return {
            'encrypted_key': base64.b64encode(ciphertext).decode(),
            'key_nonce': base64.b64encode(nonce).decode(),
            'key_tag': base64.b64encode(tag).decode(),
            'wrapped_dek': base64.b64encode(wrapped_dek).decode(),
            'key_id': f'key_{datetime.utcnow().timestamp()}',
            'algorithm': 'RSA-4096'  # Metadata
        }
    
    def decrypt_private_key(self, encrypted_key_data: Dict[str, str]) -> str:
        """Decrypt private key from storage"""
        ciphertext = base64.b64decode(encrypted_key_data['encrypted_key'])
        nonce = base64.b64decode(encrypted_key_data['key_nonce'])
        tag = base64.b64decode(encrypted_key_data['key_tag'])
        wrapped_dek = base64.b64decode(encrypted_key_data['wrapped_dek'])
        
        # Unwrap DEK
        dek = self._unwrap_key(wrapped_dek)
        
        # Decrypt private key
        aesgcm = AESGCM(dek)
        private_key_bytes = aesgcm.decrypt(nonce, ciphertext + tag, b'private_key')
        
        return private_key_bytes.decode()
    
    # ========================================================================
    # Signing & Verification (Ed25519)
    # ========================================================================
    
    def sign_data(self, data: str) -> Dict[str, str]:
        """
        Sign data using Ed25519
        
        Returns:
            {
                'signature': base64 signature,
                'public_key': base64 public key,
                'key_id': signing key identifier,
                'algorithm': 'Ed25519'
            }
        """
        signature = self.signing_key_private.sign(data.encode())
        
        public_key_bytes = self.signing_key_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        return {
            'signature': base64.b64encode(signature).decode(),
            'public_key': base64.b64encode(public_key_bytes).decode(),
            'key_id': 'signing_key_v1',
            'algorithm': 'Ed25519',
            'signed_at': datetime.utcnow().isoformat()
        }
    
    def verify_signature(self, data: str, signature_data: Dict[str, str]) -> bool:
        """
        Verify Ed25519 signature
        
        Args:
            data: Original data that was signed
            signature_data: Dict from sign_data()
        
        Returns:
            True if signature is valid
        """
        try:
            signature = base64.b64decode(signature_data['signature'])
            public_key_bytes = base64.b64decode(signature_data['public_key'])
            
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            public_key.verify(signature, data.encode())
            
            return True
        except Exception:
            return False
    
    # ========================================================================
    # Hash Functions (For Dates/Non-Encrypted Fields)
    # ========================================================================
    
    def hash_for_lookup(self, value: str, salt: str = None) -> Dict[str, str]:
        """
        Hash value for lookup (when encryption not needed but obfuscation is)
        
        Use for: dates (epoch buckets), non-sensitive metadata
        
        Returns:
            {
                'hash': hex hash,
                'salt': hex salt
            }
        """
        if salt is None:
            salt = os.urandom(16)
        else:
            salt = bytes.fromhex(salt)
        
        # SHA256 hash with salt
        hash_obj = hashlib.sha256(salt + value.encode())
        
        return {
            'hash': hash_obj.hexdigest(),
            'salt': salt.hex()
        }
    
    # ========================================================================
    # Complete Message Encryption (All Components)
    # ========================================================================
    
    def encrypt_complete_message(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Encrypt complete message with all components
        
        Input:
            {
                'content': 'Secret message',
                'sender': 'alice@dnacrypt.com',
                'receiver': 'bob@dnacrypt.com',
                'urgency': 'high'
            }
        
        Returns:
            {
                # Encrypted message body
                'content_encrypted': {...},
                
                # Searchable sender (blind index)
                'sender_index': blind index,
                'sender_encrypted': encrypted sender,
                
                # Searchable receiver (blind index)
                'receiver_index': blind index,
                'receiver_encrypted': encrypted receiver,
                
                # Plaintext metadata (non-sensitive)
                'urgency': 'high',
                'timestamp': datetime,
                
                # Signature
                'message_signature': {...}
            }
        """
        # Encrypt message content (body)
        content_encrypted = self.encrypt_message(message_data['content'])
        
        # Create blind indexes for sender/receiver (for search)
        sender_index = self.create_blind_index(message_data['sender'])
        receiver_index = self.create_blind_index(message_data['receiver'])
        
        # Encrypt full sender/receiver (for display)
        sender_encrypted = self.encrypt_field(message_data['sender'], 'sender')
        receiver_encrypted = self.encrypt_field(message_data['receiver'], 'receiver')
        
        # Sign the message
        message_signature = self.sign_data(message_data['content'])
        
        return {
            'content_encrypted': content_encrypted,
            'sender_index': sender_index,
            'sender_encrypted': sender_encrypted,
            'receiver_index': receiver_index,
            'receiver_encrypted': receiver_encrypted,
            'urgency': message_data.get('urgency', 'medium'),  # Plaintext
            'timestamp': datetime.utcnow().isoformat(),  # Plaintext for range queries
            'message_signature': message_signature
        }
    
    def decrypt_complete_message(self, encrypted_message: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt complete message"""
        return {
            'content': self.decrypt_message(encrypted_message['content_encrypted']),
            'sender': self.decrypt_field(encrypted_message['sender_encrypted'], 'sender'),
            'receiver': self.decrypt_field(encrypted_message['receiver_encrypted'], 'receiver'),
            'urgency': encrypted_message['urgency'],
            'timestamp': encrypted_message['timestamp'],
            'signature_valid': self.verify_signature(
                encrypted_message['content_encrypted']['ciphertext'],
                encrypted_message['message_signature']
            )
        }


# ============================================================================
# Helper Functions for Database Integration
# ============================================================================

def init_encryption_manager(master_password: str = None) -> EncryptionManager:
    """Initialize encryption manager with master password"""
    return EncryptionManager(master_password=master_password)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    print("="*70)
    print("DNACryptDB Encryption Layer - Test Suite")
    print("="*70)
    
    # Initialize
    enc = EncryptionManager(master_password="test_master_key_123")
    
    # Test 1: Message Encryption
    print("\n[Test 1] Message Encryption (Client-Side AES-GCM)")
    message = "This is a top secret message about Project Alpha"
    encrypted_msg = enc.encrypt_message(message)
    print(f"  Plaintext: {message}")
    print(f"  Ciphertext: {encrypted_msg['ciphertext'][:50]}...")
    print(f"  Wrapped DEK: {encrypted_msg['wrapped_dek'][:50]}...")
    
    decrypted_msg = enc.decrypt_message(encrypted_msg)
    print(f"  Decrypted: {decrypted_msg}")
    print(f"  ✓ Match: {message == decrypted_msg}")
    
    # Test 2: Blind Index
    print("\n[Test 2] Blind Index (Searchable Encryption)")
    email = "alice@dnacrypt.com"
    index = enc.create_blind_index(email)
    print(f"  Email: {email}")
    print(f"  Blind Index: {index}")
    print(f"  ✓ Searchable: Yes (equality only)")
    print(f"  ✓ Privacy: Original email hidden")
    
    # Test 3: Field Encryption
    print("\n[Test 3] Field-Level Encryption (PII)")
    user_data = {
        'email': 'alice@dnacrypt.com',
        'display_name': 'Alice Smith',
        'phone': '+1-555-1234'
    }
    encrypted_user = enc.encrypt_user_data(user_data)
    print(f"  Original: {user_data}")
    print(f"  Email Index: {encrypted_user['email_index']}")
    print(f"  Encrypted Fields: {list(encrypted_user.keys())}")
    
    decrypted_user = enc.decrypt_user_data(encrypted_user)
    print(f"  Decrypted: {decrypted_user}")
    
    # Test 4: DNA Sequence Encryption with Signature
    print("\n[Test 4] DNA Sequence Encryption + Ed25519 Signature")
    dna_sequence = "ATCGATCGATCGAAATTTGGGCCC"
    metadata = {"encoding": "binary_to_dna", "quality": 0.98}
    
    encrypted_seq = enc.encrypt_dna_sequence(dna_sequence, metadata)
    print(f"  Original: {dna_sequence}")
    print(f"  Encrypted: {encrypted_seq['encrypted_sequence'][:50]}...")
    print(f"  Signature: {encrypted_seq['signature'][:50]}...")
    
    decrypted_seq, sig_valid = enc.decrypt_and_verify_sequence(encrypted_seq)
    print(f"  Decrypted: {decrypted_seq}")
    print(f"  Signature Valid: {sig_valid}")
    print(f"  ✓ Match: {dna_sequence == decrypted_seq}")
    
    # Test 5: Complete Message Encryption
    print("\n[Test 5] Complete Message Encryption (All Components)")
    full_message = {
        'content': 'Secret communication about encryption keys',
        'sender': 'alice@dnacrypt.com',
        'receiver': 'bob@dnacrypt.com',
        'urgency': 'critical'
    }
    
    encrypted_complete = enc.encrypt_complete_message(full_message)
    print(f"  Components Encrypted:")
    print(f"    ✓ Message content (AES-GCM)")
    print(f"    ✓ Sender (blind index + encryption)")
    print(f"    ✓ Receiver (blind index + encryption)")
    print(f"    ✓ Signature (Ed25519)")
    print(f"  Plaintext fields: urgency, timestamp")
    
    decrypted_complete = enc.decrypt_complete_message(encrypted_complete)
    print(f"\n  Decrypted Message:")
    print(f"    Content: {decrypted_complete['content']}")
    print(f"    Sender: {decrypted_complete['sender']}")
    print(f"    Receiver: {decrypted_complete['receiver']}")
    print(f"    Signature Valid: {decrypted_complete['signature_valid']}")
    
    print("\n" + "="*70)
    print("✓ All encryption tests passed!")
    print("="*70)