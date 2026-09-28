# Contributing to Cloud-Native Automated Compliance and Audit System

Thank you for your interest in contributing! This project is designed as a final year capstone project demonstrating enterprise-grade RegTech capabilities.

## Development Workflow

1. **Fork & Clone**
   ```bash
   git clone https://github.com/yourusername/compliance-audit-system.git
   cd compliance-audit-system
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Follow existing code style and patterns
   - Add tests for new functionality
   - Update documentation as needed

4. **Commit & Push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

5. **Open Pull Request**

## Code Standards

### Python (Backend)
- **Formatter**: Black (line length 100)
- **Linter**: Ruff or Flake8
- **Type Hints**: Required for all public functions
- **Docstrings**: Google-style docstrings for all modules, classes, and public methods

### JavaScript/TypeScript (Frontend)
- **Formatter**: Prettier
- **Linter**: ESLint with Next.js config
- **Components**: Functional components with hooks
- **Styling**: Tailwind CSS utility classes

## Adding New Compliance Rules

To add a new compliance check:

1. Create a new service in `backend/services/` (e.g., `hr_compliance.py`)
2. Implement the `analyze(text: str) -> List[Dict]` method
3. Register the service in `backend/main.py` routing logic
4. Add rule ID constants following the pattern: `DOMAIN-XXX` (e.g., `HR-001`)
5. Add test cases in `tests/`

## Architecture Decisions

All significant architectural decisions should be documented as **ADRs (Architecture Decision Records)** in `docs/adr/`.

## Testing

```bash
# Backend tests
cd backend && python -m pytest -v --cov=.

# Frontend tests
cd frontend && npm test
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
