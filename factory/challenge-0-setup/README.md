# Challenge 0: Verify your setup

Time: ~5 minutes

You completed the setup before the workshop by following [PREREQUISITES.md](../../PREREQUISITES.md). You created your Foundry project, deployed the model, connected tracing and created `factory/.env` in the Foundry portal. This challenge only checks that everything still works.

## Check

1. Open the [Foundry portal](https://ai.azure.com) with **New Foundry** turned on, and select your project.
2. Select **Build → Models** and check that **gpt-5.4** is deployed.
3. Check that `factory/.env` exists and has your **project endpoint** and **Application Insights connection string**.
4. From the repository root, run:

```bash
python factory/smoke_test.py
```

## Success criteria

- [ ] Your project opens in the Foundry portal and **gpt-5.4** is deployed.
- [ ] `python factory/smoke_test.py` prints `Smoke test passed.`

> [!NOTE]
> If you set `FOUNDRY_API_KEY` in `.env` instead of using `az login`, the smoke test checks the model only. The agent you created in the portal (prerequisites, section 8) shows that agents work. In Challenges 1, 2 and 4, follow the **No `az login`?** steps.

If something fails, see **If something fails** in [PREREQUISITES.md](../../PREREQUISITES.md).
