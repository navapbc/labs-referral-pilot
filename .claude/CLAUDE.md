# Claude Code Instructions

## Git Workflow

- **Commit frequently**: After completing each logical unit of work (feature, fix, or significant change), commit with a descriptive message
- Follow conventional commit format: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
- Include a brief summary of what changed and why

## Project Structure

- `frontend/` - Next.js frontend application
- `app/` - Python/Flask backend with Haystack pipelines
- Both use Docker for local development (`make start` in each directory)

## Testing

- Run `npm run ts:check` in frontend to verify TypeScript
- Use Playwright for UI verification when making visual changes

## Code Style

- Frontend uses Tailwind CSS for styling
- Follow existing patterns in the codebase
- Ensure WCAG AA accessibility compliance for colors/contrast
