import asyncio
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from backend.database.database import engine
from sqlalchemy import text

async def generate_and_save_vapid():
    # 1. Generate EC Key
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    # 2. Get Raw Private Key (PKCS8 DER) then Base64
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    # Actually VAPID private key should be the raw private scalar (32 bytes)
    priv_num = private_key.private_numbers().private_value
    priv_raw = priv_num.to_bytes(32, 'big')
    
    # 3. Get Raw Public Key (Uncompressed EC point)
    # X and Y coordinates (32 bytes each) + 0x04 prefix
    pub_nums = public_key.public_numbers()
    pub_raw = b'\x04' + pub_nums.x.to_bytes(32, 'big') + pub_nums.y.to_bytes(32, 'big')

    # 4. URL-safe Base64 encoding (no padding)
    def b64url(data):
        return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

    vapid_private = b64url(priv_raw)
    vapid_public = b64url(pub_raw)

    print(f"Generated VAPID Public: {vapid_public}")
    
    # 5. Save to DB
    async with engine.begin() as conn:
        # Delete old if any
        await conn.execute(text("DELETE FROM global_settings WHERE key IN ('vapid_public_key', 'vapid_private_key')"))
        # Insert new
        await conn.execute(text("INSERT INTO global_settings (key, value) VALUES (:k1, :v1), (:k2, :v2)"), 
                           [{"k1": "vapid_public_key", "v1": vapid_public, "k2": "vapid_private_key", "v2": vapid_private}])
        print("VAPID keys saved to global_settings.")

if __name__ == "__main__":
    asyncio.run(generate_and_save_vapid())
