# Deep & Exhaustive Review (Latest Changes)

## Findings
- **Medium:** Client health refresh cannot take effect during initial connection retries because `client` is captured once before the loop; even after consecutive failures, the same client is reused for all initial attempts, which undermines the new "refresh on failure" goal and can cause avoidable request failure. (`src/gemini_research_mcp/deep.py:233`, `src/gemini_research_mcp/deep.py:364`)
- **Medium:** Reconnect path records a client success before validating that `resume_stream` is iterable; if the API returns `None` or non-iterable, the success resets failure tracking and increments request count even though the attempt fails. (`src/gemini_research_mcp/deep.py:493`, `src/gemini_research_mcp/deep.py:498`)
- **Low:** Client health metrics undercount because `interaction.error` events and polling `interactions.get` calls do not record failures or successes; `CLIENT_MAX_REQUESTS` and `consecutive_failures` may never trigger under heavy polling or API error events. (`src/gemini_research_mcp/deep.py:348`, `src/gemini_research_mcp/deep.py:611`)
- **Low:** Config comment says "1 hour of inactivity," but refresh logic is based on absolute age and idle time at half the threshold, which is more aggressive and may mislead operators tuning this value. (`src/gemini_research_mcp/config.py:56`, `src/gemini_research_mcp/deep.py:78`)

## Questions / Assumptions
- Is `genai.Client` safe to share across concurrent async requests? The new global singleton could create cross-request interference if it is not; if that is a concern, consider a per-request client or a lock around refresh. (`src/gemini_research_mcp/deep.py:110`)

## Change Summary
- Adds client health tracking, retry/backoff configuration, and reconnection logging/behavior in `deep.py`, with new retry/health constants in `config.py`.
