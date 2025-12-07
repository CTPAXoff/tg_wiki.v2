#!/bin/bash

echo "Setting up Telegram Parser..."

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file. Please edit it with your Telegram API credentials."
fi

# Setup backend
echo "Setting up backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt

# Setup frontend
echo "Setting up frontend..."
cd ../frontend
npm install

echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Telegram API credentials"
echo "2. Run backend: cd backend && source venv/bin/activate && python run.py"
echo "3. Run frontend: cd frontend && npm run dev"
echo "4. Open http://localhost:5173 in your browser"