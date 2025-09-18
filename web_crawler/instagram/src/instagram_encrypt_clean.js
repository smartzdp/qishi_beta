/**
 * Clean Instagram Password Encryption - Node.js Implementation
 * 
 * Replicates Instagram's exact encryption logic from their JavaScript source code.
 */

const crypto = require('crypto');
const nacl = require('tweetnacl');
const blake = require('blakejs');

/**
 * Convert hex string to Uint8Array
 */
function hexToBytes(hex) {
    const bytes = [];
    for (let i = 0; i < hex.length; i += 2) {
        bytes.push(parseInt(hex.substr(i, 2), 16));
    }
    return new Uint8Array(bytes);
}

/**
 * NaCl sealed box implementation (matching tweetnacl-sealedbox-js exactly)
 */
function sealedBoxSeal(message, recipientPublicKey) {
    const ephemeralKeyPair = nacl.box.keyPair();
    
    // Create nonce from Blake2b hash of both public keys (CRITICAL: matches Instagram's implementation)
    const nonceInput = new Uint8Array(ephemeralKeyPair.publicKey.length + recipientPublicKey.length);
    nonceInput.set(ephemeralKeyPair.publicKey, 0);
    nonceInput.set(recipientPublicKey, ephemeralKeyPair.publicKey.length);
    const nonce = blake.blake2b(nonceInput, null, 24); // 24 bytes for NaCl nonce
    
    // Encrypt with NaCl box
    const encrypted = nacl.box(message, nonce, recipientPublicKey, ephemeralKeyPair.secretKey);
    if (!encrypted) {
        throw new Error('NaCl encryption failed');
    }
    
    // Return ephemeral public key + encrypted message
    const result = new Uint8Array(32 + encrypted.length);
    result.set(ephemeralKeyPair.publicKey, 0);
    result.set(encrypted, 32);
    
    return result;
}

/**
 * Main encryption function matching Instagram's EnvelopeEncryption.encrypt
 */
async function encryptPassword(keyId, publicKeyHex, password, timestamp) {
    console.log(`🔐 Encrypting password: "${password}" with timestamp: ${timestamp}`);
    
    // Validate inputs
    if (publicKeyHex.length !== 64) {
        throw new Error('Invalid public key length');
    }
    
    const publicKeyBytes = hexToBytes(publicKeyHex);
    const passwordBytes = new TextEncoder().encode(password);
    const timestampBytes = new TextEncoder().encode(timestamp);
    
    console.log(`   Password bytes: ${passwordBytes.length}`);
    console.log(`   Timestamp bytes: ${timestampBytes.length}`);
    console.log(`   Public key bytes: ${publicKeyBytes.length}`);
    
    // Generate AES key
    const aesKey = crypto.randomBytes(32);
    console.log(`   AES key: ${aesKey.toString('hex')}`);
    
    // Zero IV (critical - matches Instagram's JavaScript)
    const iv = new Uint8Array(12);
    console.log(`   IV: ${Array.from(iv).map(b => b.toString(16).padStart(2, '0')).join('')}`);
    
    // AES-GCM encryption
    const key = await crypto.webcrypto.subtle.importKey(
        'raw',
        aesKey,
        { name: 'AES-GCM' },
        false,
        ['encrypt']
    );
    
    const encryptedResult = await crypto.webcrypto.subtle.encrypt(
        {
            name: 'AES-GCM',
            iv: iv,
            additionalData: timestampBytes,
            tagLength: 128
        },
        key,
        passwordBytes
    );
    
    const encryptedArray = new Uint8Array(encryptedResult);
    const ciphertext = encryptedArray.slice(0, -16);
    const authTag = encryptedArray.slice(-16);
    
    console.log(`   Ciphertext: ${Array.from(ciphertext).map(b => b.toString(16).padStart(2, '0')).join('')}`);
    console.log(`   Auth tag: ${Array.from(authTag).map(b => b.toString(16).padStart(2, '0')).join('')}`);
    
    // Encrypt AES key with sealed box
    const encryptedAesKey = sealedBoxSeal(aesKey, publicKeyBytes);
    console.log(`   Encrypted AES key length: ${encryptedAesKey.length}`);
    
    // Build envelope structure
    const envelopeSize = 1 + 1 + 2 + encryptedAesKey.length + authTag.length + ciphertext.length;
    const envelope = new Uint8Array(envelopeSize);
    
    let offset = 0;
    
    // Byte 0: Key ID
    envelope[offset++] = keyId;
    
    // Byte 1: Version (envelope version = 1)
    envelope[offset++] = 1;
    
    // Bytes 2-3: Encrypted key length (little endian)
    const keyLen = encryptedAesKey.length;
    envelope[offset++] = keyLen & 0xFF;
    envelope[offset++] = (keyLen >> 8) & 0xFF;
    
    // Encrypted AES key
    envelope.set(encryptedAesKey, offset);
    offset += encryptedAesKey.length;
    
    // Auth tag
    envelope.set(authTag, offset);
    offset += authTag.length;
    
    // Ciphertext
    envelope.set(ciphertext, offset);
    
    console.log(`   Envelope size: ${envelope.length} bytes`);
    
    // Format final result
    const base64Data = Buffer.from(envelope).toString('base64');
    const result = `#PWD_INSTAGRAM_BROWSER:10:${timestamp}:${base64Data}`;
    
    console.log(`✅ Result: ${result}`);
    return result;
}

/**
 * Simple test function - uses example keys for demonstration
 */
async function test() {
    console.log("⚠️  Test function disabled - no hardcoded keys");
    console.log("   Use the Python wrapper or provide keys manually");
    console.log("   Example: node encrypt_silent.js <keyId> <publicKey> <password> <timestamp>");
    return;
    
    console.log("Instagram Password Encryption - Clean Version");
    console.log("=" * 50);
    
    try {
        const encrypted = await encryptPassword(keyId, publicKey, password, timestamp);
        console.log(`\n📋 Copy this result:\n${encrypted}`);
    } catch (error) {
        console.error("❌ Error:", error.message);
    }
}

// Export for module use
module.exports = { encryptPassword };

// Run test if called directly
if (require.main === module) {
    test();
}
