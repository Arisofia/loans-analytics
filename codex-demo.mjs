import { Codex } from '@openai/codex-sdk'

const codex = new Codex()
const thread = codex.startThread()

const run = async () => {
  const result = await thread.run(
    'Make a plan to diagnose and fix the CI failures'
  )
  console.log(result)
}

run().catch(console.error)
