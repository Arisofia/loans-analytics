'use client'

import { IntegrationSettings } from '@/components/integrations/IntegrationSettings'
import { SlideLayout } from '@/components/layout/SlideLayout'
import { SlideShell } from '@/components/layout/SlideShell'

export default function IntegrationsPage() {
  return (
    <SlideShell slideNumber={2}>
      <SlideLayout
        section="Deck 2"
        title="Integration Settings"
        subtitle="Connect social and custom platforms to keep your dashboards fresh."
      >
        <IntegrationSettings />
      </SlideLayout>
    </SlideShell>
  )
}
