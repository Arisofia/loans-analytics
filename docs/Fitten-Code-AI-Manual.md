# Fitten Code AI Assistant Manual
## Product overview

Fitten Code AI (by Fittentech) is a developer-focused coding assistant that can handle code reviews, test suggestions,
deployment script generation, and more across local and cloud environments. This guide helps the
`abaco-loans-analytics` repo integrate Fitten Code AI end-to-end, from development through deployment.
## Installation steps

1. Prepare the basics: Git, Python 3.10+, Node.js (for the web project), Docker (optional for containerization).
2. Download the Fitten Code AI model and config to secure storage—do not commit them to Git. Per your org policy, place
   them under `/opt/fitten/models`, a shared volume, or a model server.
3. Create `fitten.config.toml` (or the org-approved file) at the repo root and point it to the model path:
   ```toml
   [model]
   path = "/absolute/or/network/path/to/fitten-model"
   cache_dir = ".fitten/cache"
   ```
4. Install the Fitten CLI or SDK (example):
   ```bash
   pip install fitten-cli
   fitten login        # add if authentication is required
   ```
5. Add Fitten commands or scripts to `package.json` `scripts` (web) or the `Makefile` (analytics) so developers can run
   them with one command.
## Feature highlights

- **Instant code analysis**: runs automatically in PRs, commits, or CI and provides inline-style feedback.
- **Deployment assistant**: generates deployment summaries, Azure scripts, and CI/CD configs to reduce ops friction.
- **Developer guidance**: tailored recommendations for `apps/web` and `apps/analytics`, including testing coverage tips
  and model performance checks.
- **Multi-tool integration**: works with GitHub Actions, Azure Pipelines, and the Fitten local CLI to close the
  develop–test–deploy–monitor loop.
## Local and GitHub integration tips

1. Local: set the `FITTEN_CONFIG` environment variable in your shell so Fitten CLI can read `fitten.config.toml`. Use
   commands like `fitten sniff apps/web` to scan subprojects as needed.
2. GitHub: add `fitten.yml` under `.github/workflows/` to trigger Fitten checks on `pr` and `push`, with Slack/Webhook
   notifications.
3. Deployment: Fitten can generate Azure/Vercel deployment notes and autofill variables using the scripts under
   `infra/azure`.
4. Opportunities: route Fitten output into Jira/Notion so recommendations become actionable tasks and every opportunity
   is tracked to closure.
## FAQ

- **Q: Do Fitten models have to live in the repo?**
  A: No. Do not commit model files. Just store the path in `fitten.config.toml` and download or mount in CI if needed.
- **Q: How do I debug Fitten’s suggestions?**
  A: Run `fitten explain <file>` locally, use `--preview` to inspect context, and mark whether suggestions are accepted
  in the PR.
- **Q: How does Fitten work with SonarCloud or OpenAI?**
  A: Use Fitten as the first review layer, then run SonarCloud for static analysis. OpenAI can handle more complex
  generation; they complement one another.
## Contact

Fittentech (Fitten Code) technical support:

- Website: https://www.fittentech.com/
- Fitten Code platform: https://code.fittentech.com/
- Reach out via the platform or corporate email for licensing and help.
## Useful links

- Fitten Code platform: https://code.fittentech.com/
- Fittentech corporate site: https://www.fittentech.com/
- `abaco-loans-analytics` repository (this page): https://github.com/9nnxqzyq4y-eng/abaco-loans-analytics
## Test local inference

After confirming the model path, you can quickly validate Fitten local inference with Hugging Face Transformers:
```python
from transformers import AutoTokenizer, AutoModelForCausalLM
model_path = "/absolute/or/network/path/to/fitten-model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)
prompt = "Fitten Code AI makes coding more confident."
inputs = tokenizer(prompt, return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=64)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```
If the model is not local, download it in CI (for example, with `wget` + `unzip`) and pass the path to the
`huggingface` API or Fitten CLI. This run is only to ensure the model loads, the tokenizer is readable, and the
inference loop is wired correctly.
