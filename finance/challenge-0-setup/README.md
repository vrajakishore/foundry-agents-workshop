# Challenge 0: Verify your setup

Time: ~5 minutes

You completed the setup before the workshop with [PREREQUISITES.md](../../PREREQUISITES.md). The finance track uses the same project, model and `.env` file as the factory track.

## Check

1. Open the [Foundry portal](https://ai.azure.com) and select **your own** project, `<your-alias>-workshop`.
2. Select **Build → Models**. Check that **gpt-5.4** is deployed. For Challenge 5, also check for **gpt-5.4-mini**. It is optional.
3. Check that `factory/.env` exists and has your **project endpoint** and **Application Insights connection string**. The endpoint must end with `/api/projects/<your-alias>-workshop`.
4. From the repository root, run:

    ```bash
    python factory/smoke_test.py
    ```

The finance scripts read `finance/.env` if it exists. If it doesn't, they read `factory/.env`. You don't need a second file.

## Success criteria

- [ ] Your project opens in the Foundry portal and **gpt-5.4** is deployed.
- [ ] The endpoint in `factory/.env` points to your own project.
- [ ] `python factory/smoke_test.py` prints `Smoke test passed.`

> [!NOTE]
> **No `az login`?** If you set `FOUNDRY_API_KEY` in `.env`, the smoke test checks the model only. In Challenges 1 and 2, follow the **No `az login`?** steps.

If something fails, see **If something fails** in [PREREQUISITES.md](../../PREREQUISITES.md).
