# Sports Betting Arbitrage
Sports Betting Arbitrage Calculator. Uses Python and API from The Odds API.

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/YOUR-USERNAME/Sports-Betting-Arbitrage.git
cd Sports-Betting-Arbitrage
```

### 2. Get your API key(s)
Go to https://the-odds-api.com/#get-access and get your API key. The free tier includes 500 requests/month. Note: On average, this program requires ~1500 credits, so more free keys or a paid tier may be required for optimal results.

### 3. Add your API key(s)
Create a new file called `.env` in the project directory.

**Single API key:**
```
API_KEY=your_api_key_here
```

**Multiple API keys:**
```
API_KEYS=key1,key2,key3
```

### 4. (OPTIONAL) Add Email Functionality
In the `.env` file, set the following variables:
```bash
SMTP_HOST=SMTP_HOST (look online to see what to put based on outlook, gmail, etc.)
SMTP_PORT=587
SMTP_USER=sending_email_address
SMTP_PASSWORD=sending_email_address_password
ALERT_EMAIL=receiving_email_address
MIN_ROI_ALERT=minimum_roi_to_display_in_email
```

### 5. Run the program

Choose one of the following options:

---

## Option A: Docker (Recommended)

Requires [Docker Desktop](https://www.docker.com/products/docker-desktop/) to be installed and running.

**Using Docker Compose:**
```bash
docker-compose build arbitrage
docker-compose run arbitrage
```

**Or using Docker directly:**
```bash
docker build -t arbitrage-calc .
docker run -it --env-file .env arbitrage-calc
```

---

## Option B: Python

Requires Python 3.8+ installed.

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Run the program:**
```bash
python arbitrageCalculator.py
```
