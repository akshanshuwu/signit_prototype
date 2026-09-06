# VeraScan

Face Identification & Blockchain Verification

VeraScan is a face-to-blockchain verification system that discovers where a face appears online, independently verifies candidate matches, creates a cryptographic fingerprint of the evidence, and anchors that fingerprint on the Ethereum blockchain.

Try VeraScan

Live website: https://verascan-tewz.vercel.app

The live website provides the complete user-facing verification experience.

## How It Works

- Face Detection — YuNet
- Face Encoding — SFace 128-D
- Web Discovery — Google Lens via SerpAPI
- Independent Verification — cosine similarity
- Evidence Fingerprinting — SHA-256 using the canonical source page URL and candidate image bytes
- Blockchain Registration — Ethereum Sepolia
- Re-verification — read the recorded blockchain data and recompute the fingerprint
- Tamper Detection — detect changes in the evidence

The blockchain verifies the integrity of the recorded evidence. It does not prove identity or account ownership.

## Backend CLI

The backend includes a command-line interface for running the complete verification pipeline without the frontend.

### Scan

```bash
cd backend
source venv/bin/activate
python main.py scan --image ../download.jpeg
```

The scan shows:

- Face detection
- 128-dimensional SFace embedding
- Google Lens discovery
- Candidate verification
- Biometric similarity scores
- Full source/page URLs for discovered candidates
- Best verified source URL
- SHA-256 evidence fingerprint
- Ethereum Sepolia transaction
- On-chain read-back verification
- Record ID
- Receipt JSON

The CLI presents each verification stage, candidate similarity scores, evidence fingerprint, and blockchain status directly in the terminal.

### Re-verify a Record

After a scan, the terminal prints the exact Record ID needed for re-verification.

```bash
python main.py verify --record <record_id>
```

This retrieves the blockchain record, recomputes the evidence fingerprint, and verifies that the local fingerprint matches the on-chain fingerprint.

### Demonstrate Tamper Detection

```bash
python main.py verify --record <record_id> --tamper
```

This temporarily changes the evidence in memory, recomputes the fingerprint, and demonstrates that the modified fingerprint no longer matches the value stored on-chain.

The original receipt and evidence are not modified.

### CLI Help

```bash
python main.py --help
python main.py scan --help
python main.py verify --help
```

### Run Tests

```bash
python -m pytest tests/ -v
```

## Tech Stack

### Frontend

- Next.js
- React
- TypeScript
- ethers.js

### Backend

- Python
- FastAPI
- OpenCV
- YuNet
- SFace
- SerpAPI
- Google Lens

### Blockchain

- Solidity
- Ethereum Sepolia
- Alchemy RPC

## Local Development

### Hosted Application

Open:

https://verascan-tewz.vercel.app

No local setup is required.

### Full Local Application

Run the backend:

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

Then, in another terminal, run the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open the local frontend shown by Next.js.

### Backend Only

```bash
cd backend
source venv/bin/activate
python main.py scan --image ../download.jpeg
```

Then use the printed Record ID for re-verification and tamper detection.

### Prerequisites

For local development, you will need:

- Python 3.12+
- Node.js 18+
- npm
- Internet connection
- SerpAPI account/API key
- Ethereum Sepolia RPC
- A dedicated Sepolia test wallet with test ETH for local blockchain write operations

### Environment Variables

Create the required environment files from the provided .env.example files.

Backend:

```env
SERPAPI_KEY=your_serpapi_key
FACE_MATCH_THRESHOLD=0.50
ALCHEMY_RPC_URL=your_sepolia_rpc_url
CONTRACT_ADDRESS=0x0fb9824673d027Fb2f2fC629706C2e1E24C39408
DEPLOYER_PRIVATE_KEY=your_sepolia_wallet_private_key
CORS_ORIGINS=http://localhost:3000
```

Frontend:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_CONTRACT_ADDRESS=0x0fb9824673d027Fb2f2fC629706C2e1E24C39408
NEXT_PUBLIC_ALCHEMY_RPC_URL=your_sepolia_rpc_url
```

For local execution, users should provide their own API credentials and test wallet. The deployed application keeps server-side credentials configured on the backend and does not require judges or users to enter them.

Never commit API keys, private keys, or other secrets. Never use a wallet containing real funds for local blockchain testing.

## Blockchain

Network: Ethereum Sepolia

Contract:

```text
0x0fb9824673d027Fb2f2fC629706C2e1E24C39408
```

VeraScan stores the verification record and evidence fingerprint on-chain.

The actual image is not stored on the blockchain.

## Evidence Verification

VeraScan uses:

- YuNet for face detection
- SFace for face recognition
- 128-dimensional normalized face embeddings
- Cosine similarity for independent candidate verification
- A configurable face-match threshold

Default threshold:

```text
0.50
```

The system reports biometric similarity, not identity probability.

For evidence integrity, VeraScan generates:

```text
SHA-256(
    canonical source page URL
    +
    raw candidate image bytes
)
```

The resulting fingerprint is anchored on Ethereum Sepolia.

## Verification Flow

```text
Input Image
    ↓
Face Detection
    ↓
SFace Face Encoding
    ↓
Google Lens Discovery
    ↓
Candidate Images
    ↓
Independent Face Verification
    ↓
Best Verified Source
    ↓
SHA-256 Evidence Fingerprint
    ↓
Ethereum Sepolia
    ↓
Record ID
    ↓
Re-verification
```

## Tamper Detection

```text
Original Evidence
       ↓
    SHA-256
       ↓
On-chain Fingerprint
       ↓
Modified Evidence
       ↓
    SHA-256
       ↓
Compare
       ↓
Mismatch → Tampering Detected
```

## Privacy

VeraScan does not normally persist the uploaded input image on the application server.

To perform Google Lens reverse-image search, a temporary cropped face image may be uploaded to an external image-hosting service solely to enable the search.

Images are not stored on-chain. Only the cryptographic verification data is recorded on the blockchain.

## Models

VeraScan uses:

- YuNet — face detection
- SFace — face recognition

The models are downloaded lazily into:

```text
backend/models/
```

They are excluded from Git.

## Project Structure

```text
VeraScan/
├── backend/
│   ├── services/
│   ├── tests/
│   ├── receipts/
│   ├── models/
│   └── main.py
│
├── contracts/
│
├── frontend/
│
├── .env.example
├── .gitignore
└── README.md
```

## Limitations

- Reverse-image discovery depends on Google Lens and SerpAPI availability.
- Web search results can contain false positives or false negatives.
- Biometric similarity is not proof of legal identity.
- A matching social-media image does not prove account ownership.
- Source pages can change or become unavailable.
- Temporary external image hosting is used to enable reverse-image search.
- Blockchain verification proves the integrity of the recorded evidence fingerprint, not the truth of the underlying identity claim.

## Backend Command Sequence

```bash
cd backend
source venv/bin/activate

python main.py scan --image ../download.jpeg

python main.py verify --record <record_id>

python main.py verify --record <record_id> --tamper

python -m pytest tests/ -v
```

## Hacker House Goa 2026

Built for Hacker House Goa 2026 — Task 3: Face Identification & Blockchain Verification.

The project demonstrates the complete flow from face detection and web discovery to independent biometric verification, cryptographic evidence fingerprinting, blockchain anchoring, re-verification, and tamper detection.
