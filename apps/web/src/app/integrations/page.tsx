import { IntegrationSettings } from '@/components/integrations/IntegrationSettings'
import { SlideShell } from '@/components/integrations/SlideShell'

export default function IntegrationsPage() {
  return (
    <SlideShell
      slideNumber={3}
      title="Integrations"
      subtitle="Secure token intake with initial syncs and per-provider controls"
    >
      <IntegrationSettings />
    </SlideShell>
  )
}
