# AI-5 Autonomous Visual Iteration: setup and operating guide

This workflow is independent of ChatGPT Work and Codex. It uses GitHub Actions as the scheduler/runner and the OpenAI API as the callable vision-and-code model.

## Required one-time repository configuration

1. Open repository **Settings → Secrets and variables → Actions → New repository secret**.
2. Add secret `OPENAI_API_KEY` with an API key from an OpenAI API project that has billing/usage enabled. Do not put the key in source files, workflow inputs, commit messages, or Linear.
3. Open **Settings → Secrets and variables → Actions → Variables → New repository variable**.
4. Add `OPENAI_MODEL` and set it to a model ID actually enabled for that API project and supporting image input. The workflow deliberately does not guess an API model ID.
5. Open **Actions → AI-5 Autonomous Visual Iteration → Run workflow**. Select branch `ai-5-modern-residence-modeling`, choose 2 rounds initially, and optionally enter the model ID. Run only after the secret and model variable are configured.

## What one run does

- Installs Blender on a GitHub-hosted Ubuntu runner and probes whether an NVIDIA GPU is exposed.
- Renders all three cameras from `scripts/ai5_modern_residence.py`.
- Sends the actual PNGs to the configured model using the OpenAI Responses API.
- If the visual reviewer reports meaningful defects, asks the model for a unified diff restricted to `scripts/ai5_modern_residence.py`.
- Checks the patch's changed paths, runs `git apply --check`, applies it only in the temporary runner workspace, checks Python syntax, and renders the next round.
- Uploads each round's images, blend file, logs, review JSON, proposed patch, final script and summary as an Actions artifact.

## Safety and limitations

- Maximum rounds are clamped to 1–3. Start with 2.
- Model-generated changes are **not automatically pushed or committed**. Review `final_scene_script.py` and the patch artifact before committing changes to the branch.
- A model's visual acceptance is a heuristic, not a guarantee of geometry correctness or commercial photorealism. Keep human visual acceptance for final delivery.
- GitHub-hosted runners are ephemeral and normally CPU-only. This does not create a persistent Blender server.
- OpenAI API usage is billed separately from a ChatGPT subscription. Configure spending limits/alerts in the API project.
- Workflow push/manual-dispatch triggers work on this development branch. GitHub scheduled workflows only run from the default branch; do not add a frequent schedule until the workflow is reviewed and merged to the default branch.
- If the API secret or model variable is missing, the workflow fails at the configuration check before sending any request.
- If the API returns a model/access/format error, inspect the workflow log. Never paste the API key into the log to debug it.

## Run and evidence

- Workflow: `.github/workflows/ai5-autonomous-iteration.yml`
- Controller: `scripts/ai5_autonomous_iteration.py`
- Output artifact: `ai5-autonomous-iteration-evidence`
- Each round: `outputs/autonomous/round_XX/`
- Summary: `outputs/autonomous/iteration_summary.json`

## What is not implemented

There is no direct callback from GitHub into the current ChatGPT conversation. The API model performs the bounded visual-analysis/revision loop inside the runner. If the user wants a separate notification to a chat app, add a webhook secret for that app; never expect an Actions event to wake the current ChatGPT session.
