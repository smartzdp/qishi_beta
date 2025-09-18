/**
 * Decode Instagram encrypted password to show structure
 */

function decodeInstagramPassword(encryptedPassword) {
    console.log("🔍 Decoding Instagram encrypted password structure");
    console.log("=" * 60);
    
    // Parse components
    const parts = encryptedPassword.split(':');
    if (parts.length !== 4) {
        console.log(`❌ Invalid format: expected 4 parts, got ${parts.length}`);
        return;
    }
    
    const [tag, version, timestamp, base64Data] = parts;
    
    console.log(`📋 COMPONENTS:`);
    console.log(`   Tag: ${tag}`);
    console.log(`   Version: ${version}`);
    console.log(`   Timestamp: ${timestamp}`);
    console.log(`   Base64 length: ${base64Data.length} characters`);
    console.log();
    
    // Decode base64
    try {
        const envelopeBytes = Buffer.from(base64Data, 'base64');
        console.log(`🔧 ENVELOPE ANALYSIS:`);
        console.log(`   Total envelope length: ${envelopeBytes.length} bytes`);
        console.log(`   Envelope hex: ${envelopeBytes.toString('hex')}`);
        console.log();
        
        if (envelopeBytes.length < 4) {
            console.log("❌ Envelope too short");
            return;
        }
        
        let offset = 0;
        
        // Key ID (1 byte)
        const keyId = envelopeBytes[offset];
        console.log(`   Offset ${offset}: Key ID = ${keyId}`);
        offset += 1;
        
        // Version (1 byte)
        const envVersion = envelopeBytes[offset];
        console.log(`   Offset ${offset}: Envelope version = ${envVersion}`);
        offset += 1;
        
        // Encrypted key length (2 bytes, little endian)
        const keyLen = envelopeBytes[offset] | (envelopeBytes[offset + 1] << 8);
        console.log(`   Offset ${offset}-${offset+1}: Encrypted AES key length = ${keyLen} bytes`);
        offset += 2;
        
        if (offset + keyLen > envelopeBytes.length) {
            console.log("❌ Invalid key length");
            return;
        }
        
        // Encrypted AES key
        const encryptedAesKey = envelopeBytes.slice(offset, offset + keyLen);
        console.log(`   Offset ${offset}-${offset + keyLen - 1}: ENCRYPTED AES KEY (${encryptedAesKey.length} bytes)`);
        console.log(`      Encrypted AES key (hex): ${encryptedAesKey.toString('hex')}`);
        console.log(`      ⚠️  This is ENCRYPTED with Instagram's public key - original AES key cannot be recovered!`);
        offset += keyLen;
        
        // AES tag (16 bytes)
        if (offset + 16 > envelopeBytes.length) {
            console.log("❌ Not enough bytes for AES tag");
            return;
        }
        
        const aesTag = envelopeBytes.slice(offset, offset + 16);
        console.log(`   Offset ${offset}-${offset + 15}: AES auth tag (${aesTag.length} bytes)`);
        console.log(`      Tag hex: ${aesTag.toString('hex')}`);
        offset += 16;
        
        // Ciphertext (remaining bytes)
        const ciphertext = envelopeBytes.slice(offset);
        console.log(`   Offset ${offset}-${envelopeBytes.length - 1}: Password ciphertext (${ciphertext.length} bytes)`);
        console.log(`      Ciphertext hex: ${ciphertext.toString('hex')}`);
        
        console.log(`\n🔐 SECURITY ANALYSIS:`);
        console.log(`   ✅ AES key is encrypted with Instagram's public key (NaCl sealed box)`);
        console.log(`   ✅ Only Instagram can decrypt the AES key with their private key`);
        console.log(`   ✅ Even with the encrypted data, the original AES key is protected`);
        console.log(`   ✅ Password is encrypted with AES-GCM using the protected AES key`);
        
    } catch (error) {
        console.log(`❌ Decode error: ${error.message}`);
    }
}

// Your encrypted password
const encryptedPassword = "#PWD_INSTAGRAM_BROWSER:10:1758156992:UQFQAD8P655zA/cEn1UYFgiB4kXPNRmZLRii4OrX6ZXN+SB4i9zcOp0+eBAZdwWj5+aKLGsZpSxzbMudegTUdzTARaFCX7PyxDVxeSltxBK+VsYi/OGtmqahNndb+Fmk35ZTtdFpYMfce79z";

decodeInstagramPassword(encryptedPassword);
