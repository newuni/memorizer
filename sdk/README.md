# SDKs (lightweight)

## Python

```python
from sdk.python.memorizer_sdk import MemorizerClient

c = MemorizerClient("http://localhost:8000", "dev-secret-change-me")
c.add_memory("User likes Docker", meta={"type": "preference"})
print(c.context("How should I deploy?"))
print(c.profile(q="deploy"))
```

## JavaScript

```js
import { MemorizerClient } from "./sdk/js/index.js";

const c = new MemorizerClient("http://localhost:8000", "dev-secret-change-me");
await c.addMemory("User likes Docker", "default", { type: "preference" });
console.log(await c.context("How should I deploy?"));
console.log(await c.profile("default", "deploy"));
```
