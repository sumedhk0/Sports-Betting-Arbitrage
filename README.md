# Sports-Betting-Arbitrage
Sports Betting Arbitrage Calculator. Uses Python and API from The Odds API.

## TO USE:
### 1. Install the required dependencies:
`pip install -r requirements.txt`

### 2. Get your API key(s):
Go to https://the-odds-api.com/#get-access and get your API key. The free tier includes 500 requests/month. Note: On average, this program requires ~1500 credits, so more free keys or a paid tier may be required for optimal results.

### 3. Add your API key(s):
Create a new file called .env in the project.

If you only have 1 API key:
Add the following line (without the parentheses):

`API_KEY=(your API key)`

Example:

`API_KEY=key`

If you have multiple API keys:
Add the following line instead (without the parentheses):

`API_KEYS=(your API keys, comma separated, no spaces, 1 line, no quotes)`

Example:

`API_KEYS=key1,key2,key3,key4`

### 4. Run the program in the terminal and get your arbitrage opportunities!
