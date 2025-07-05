# Developer Guide

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Git

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/wakedock.git
cd wakedock
```

2. Set up the backend:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

3. Set up the frontend:
```bash
cd dashboard
npm install
```

4. Configure environment:
```bash
cp config/config.example.yml config/config.yml
# Edit config.yml with your settings
```

### Running for Development

1. Start the development stack:
```bash
docker-compose up -d postgres redis
```

2. Run the backend:
```bash
python dev_server.py
```

3. Run the frontend:
```bash
cd dashboard
npm run dev
```

### Testing

Run all tests:
```bash
# Backend tests
python -m pytest

# Frontend tests
cd dashboard
npm test
```

## Code Structure

- `/src/wakedock/` - Backend Python code
- `/dashboard/` - Frontend SvelteKit code
- `/docker/` - Docker configurations
- `/docs/` - Documentation
- `/tests/` - Test files

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## Coding Standards

- Follow PEP 8 for Python code
- Use TypeScript for frontend code
- Write comprehensive tests
- Document public APIs
- Use conventional commits
