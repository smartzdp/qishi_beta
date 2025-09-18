/**
 * Silent Instagram password encryption for Python wrapper
 * Outputs only the encrypted result without console logging
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
 * NaCl sealed box implementation with Blake2b nonce
 */
function sealedBoxSeal(message, recipientPublicKey) {
    const ephemeralKeyPair = nacl.box.keyPair();
    
    // Blake2b nonce generation
    const nonceInput = new Uint8Array(ephemeralKeyPair.publicKey.length + recipientPublicKey.length);
    nonceInput.set(ephemeralKeyPair.publicKey, 0);
    nonceInput.set(recipientPublicKey, ephemeralKeyPair.publicKey.length);
    const nonce = blake.blake2b(nonceInput, null, 24);
    
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
 * Silent encryption function (no console output)
 */
async function encryptPasswordSilent(keyId, publicKeyHex, password, timestamp) {
    // Validate inputs
    if (publicKeyHex.length !== 64) {
        throw new Error('Invalid public key length');
    }
    
    const publicKeyBytes = hexToBytes(publicKeyHex);
    const passwordBytes = new TextEncoder().encode(password);
    const timestampBytes = new TextEncoder().encode(timestamp);
    
    // Generate AES key
    const aesKey = crypto.randomBytes(32);
    
    // Zero IV (matching Instagram)
    const iv = new Uint8Array(12);
    
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
    
    // Encrypt AES key with sealed box
    const encryptedAesKey = sealedBoxSeal(aesKey, publicKeyBytes);
    
    // Build envelope
    const envelope = new Uint8Array(1 + 1 + 2 + encryptedAesKey.length + authTag.length + ciphertext.length);
    let offset = 0;
    
    envelope[offset++] = 1;  // envelope version
    envelope[offset++] = keyId;  // key ID
    envelope[offset++] = encryptedAesKey.length & 0xFF;  // key length low
    envelope[offset++] = (encryptedAesKey.length >> 8) & 0xFF;  // key length high
    
    envelope.set(encryptedAesKey, offset);
    offset += encryptedAesKey.length;
    envelope.set(authTag, offset);
    offset += authTag.length;
    envelope.set(ciphertext, offset);
    
    // Format result
    const base64Data = Buffer.from(envelope).toString('base64');
    const result = `#PWD_INSTAGRAM_BROWSER:10:${timestamp}:${base64Data}`;
    
    return result;
}

// Export for module use
module.exports = { encryptPassword: encryptPasswordSilent };

// Command line interface - only output the result
if (require.main === module) {
    const args = process.argv.slice(2);
    
    if (args.length < 4) {
        console.error('Usage: node encrypt_silent.js <keyId> <publicKey> <password> <timestamp>');
        process.exit(1);
    }
    
    const [keyId, publicKey, password, timestamp] = args;
    
    encryptPasswordSilent(parseInt(keyId), publicKey, password, timestamp)
        .then(result => {
            console.log(result);  // Only output the result
            process.exit(0);
        })
        .catch(error => {
            console.error('ERROR:' + error.message);
            process.exit(1);
        });
}
