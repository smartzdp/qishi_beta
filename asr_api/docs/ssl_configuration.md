# SSL Certificate Configuration

## Overview

Whisper ASR Service supports flexible SSL certificate configuration for downloading Whisper models. This document explains how to configure SSL certificates for different environments.

## Environment Variables

### `DISABLE_SSL_VERIFICATION`

Disable SSL certificate verification (development/test only).

**Default**: `false`

**Usage**:
```bash
export DISABLE_SSL_VERIFICATION=true
```

**Warning**: Only use this in development/test environments. Never use in production.

### `SSL_CA_CERT_PATH`

Path to a custom CA certificate bundle file.

**Default**: None (uses system default or certifi)

**Usage**:
```bash
export SSL_CA_CERT_PATH=/path/to/ca-bundle.crt
```

### `REQUESTS_CA_BUNDLE`

Path to CA certificate bundle for requests library (alternative to SSL_CA_CERT_PATH).

**Default**: None

**Usage**:
```bash
export REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt
```

### `FLASK_ENV` or `ENVIRONMENT`

Set to `production` to enable production SSL certificate handling.

**Default**: `development`

**Usage**:
```bash
export FLASK_ENV=production
# or
export ENVIRONMENT=production
```

## Configuration Examples

### Development/Test Environment

For development and testing, you can disable SSL verification:

```bash
export DISABLE_SSL_VERIFICATION=true
python run.py
```

### Production Environment

For production, use proper SSL certificates:

#### Option 1: Use certifi (Recommended)

Install certifi:
```bash
pip install certifi
```

The application will automatically use certifi's certificate bundle.

#### Option 2: Use Custom CA Certificate Bundle

```bash
export FLASK_ENV=production
export SSL_CA_CERT_PATH=/path/to/ca-bundle.crt
python run.py
```

#### Option 3: Use System Default Certificates

```bash
export FLASK_ENV=production
python run.py
```

The application will use the system's default SSL certificates.

## Troubleshooting

### SSL Certificate Verification Failed

**Error**: `CERTIFICATE_VERIFY_FAILED` or `SSL: CERTIFICATE_VERIFY_FAILED`

**Solutions**:

1. **Development/Test**: Disable SSL verification
   ```bash
   export DISABLE_SSL_VERIFICATION=true
   ```

2. **Production**: Install certifi
   ```bash
   pip install certifi
   ```

3. **Production**: Use custom CA certificate bundle
   ```bash
   export SSL_CA_CERT_PATH=/path/to/ca-bundle.crt
   ```

4. **Production**: Update system certificates
   - macOS: Update certificates via system preferences
   - Linux: Update ca-certificates package
   - Windows: Update Windows certificates

### Network Connection Issues

**Error**: `Connection` or `timeout` errors

**Solutions**:

1. Check network connectivity
2. Check firewall settings
3. Verify proxy settings (if using a proxy)
4. Check if the Whisper model download server is accessible

### Certificate Bundle Not Found

**Error**: Certificate bundle file not found

**Solutions**:

1. Verify the path to the certificate bundle file
2. Check file permissions
3. Use absolute paths instead of relative paths
4. Install certifi: `pip install certifi`

## Best Practices

### Development/Test

- Use `DISABLE_SSL_VERIFICATION=true` only when necessary
- Document why SSL verification is disabled
- Remove SSL verification disabling before deploying to production

### Production

- Always use proper SSL certificates
- Install certifi for reliable certificate handling
- Use custom CA certificate bundles if needed
- Monitor SSL certificate expiration
- Update certificates regularly

## Security Considerations

1. **Never disable SSL verification in production**
   - Disabling SSL verification exposes the application to man-in-the-middle attacks
   - Always use proper SSL certificates in production

2. **Use trusted certificate authorities**
   - Only use certificates from trusted CAs
   - Verify certificate chain integrity
   - Check certificate expiration dates

3. **Keep certificates updated**
   - Regularly update CA certificate bundles
   - Monitor certificate expiration
   - Update system certificates regularly

4. **Protect certificate files**
   - Use appropriate file permissions
   - Store certificates securely
   - Don't commit certificates to version control

## Additional Resources

- [certifi documentation](https://github.com/certifi/python-certifi)
- [Python ssl module documentation](https://docs.python.org/3/library/ssl.html)
- [Requests SSL documentation](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)

