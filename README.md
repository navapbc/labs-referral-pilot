# GenAI Referral Tool

*AI-assisted resource referral and action planning for Goodwill case managers.*

## Table of Contents

- [Product Description](#product-description)
- [Architecture](#architecture)
- [Setup](#setup)
  - [Backend (app)](#backend-app)
  - [Frontend](#frontend)
- [Usage Examples](#usage-examples)
- [Contact](#contact)
- [Open Source](#open-source)

---

## Product Description

The GenAI Referral Tool is a pilot application developed by NavaLabs, a research and development team within Nava PBC, in partnership with Goodwill. It assists case managers in identifying relevant community resources and generating personalized action plans for Goodwill clients. Case managers enter client information into the tool, which uses a Retrieval-Augmented Generation (RAG) pipeline and a large language model to surface trusted resources and create a tailored action plan. Results can be printed or emailed directly to clients.

The pilot aimed to assess the effectiveness of LLMs at identifying relevant resources, and evaluated the accuracy of identifying prerequisite steps and constraints relevant to case managers' clients. Over the course of the pilot, generative AI tools were increasingly incorporated into the development workflow to expedite prototyping of frontend components.

---

### Components

| Component | Technology | AWS Service | Role |
|---|---|---|---|
| Frontend | Next.js / React | ECS | Case manager UI — enter client info, view referrals & action plan, print/email results |
| Backend / API | Python / Hayhooks | ECS | LLM pipeline orchestration, streaming and synchronous API endpoints |
| Database | PostgreSQL | RDS | Stores LLM responses, user data, and monitoring trace data |
| Vector Database | ChromaDB | ECS | RAG retrieval — improves referral speed and accuracy |
| Knowledge Base | File storage | S3 | Trusted community resources and job listings used by the RAG system |
| Email Service | AWS SES | SES | Sends referral lists and action plans to case managers and clients |
| Monitoring | Phoenix Arize | ECS | LLM trace data and prompt version management |

---

## Setup

### Backend (app)

See [docs/app/getting-started.md](docs/app/getting-started.md) for full setup instructions.

**Quick start** (from `app/`):

```bash
make init start
```

Then navigate to `localhost:3000/docs` for the Swagger UI.

### Frontend

See [frontend/README.md](frontend/README.md) for full setup instructions.

**Quick start** (from `frontend/`):

```bash
npm install
npm run dev
```

Then navigate to `localhost:3001`.

---

## Usage Examples

The following describes a typical end-to-end session for a case manager using the GenAI Referral Tool.

1. **Open the tool** — Navigate to the application in a browser.
2. **Enter client information** — Fill out the intake form with details such as the client's employment goals, barriers to employment, and location. The UI components are designed to structure this input in a way that automatically enriches the LLM prompt, reducing the need for case managers to manually phrase queries.
3. **Generate referrals** — Submit the form to trigger the RAG pipeline. The tool retrieves relevant resources from the knowledge base and passes them along with the client context to the LLM, which returns a structured list of community resources.
4. **Review resources** — Browse the returned resource list. Each resource includes relevant details to help the case manager assess fit for the client.
5. **Generate an action plan** — With resources selected, request an action plan. The LLM uses the client information and resource list to produce a personalized, step-by-step plan that accounts for prerequisite steps and constraints specific to the client's situation.
6. **Share results** — Print the referral list and action plan as a PDF, or email them directly to the client or relevant parties.

---

## Contact

For questions about this project, reach out to the NavaLabs team at [labs-dst@navapbc.com](mailto:labs-dst@navapbc.com).

---

## Open Source

This project is made available as open source for future research purposes. It was developed by [Nava PBC](https://www.navapbc.com) in partnership with Goodwill.
