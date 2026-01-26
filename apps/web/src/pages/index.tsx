import Head from 'next/head'
import { AccountConfigurationForm } from '@/components/account/AccountConfigurationForm'
import { AuthenticationForm } from '@/components/auth/AuthenticationForm'
const HomePage = () => (
  <>
    <Head>
      <title>Abaco Financial Intelligence</title>
    </Head>
    <main className="min-h-screen bg-slate-950 px-6 py-10 text-slate-100">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-10">
        <header className="space-y-2">
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            Abaco Intelligence Platform
          </p>
          <h1 className="text-3xl font-semibold">
            Operational controls for secured lending portfolios
          </h1>
          <p className="max-w-2xl text-sm text-slate-300">
            Connect authentication and account configuration to activate data
            ingestion, KPI exports, and compliance-ready analytics workflows.
          </p>
        </header>
        <section className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
            <h2 className="text-lg font-semibold">Secure access</h2>
            <p className="mt-1 text-xs text-slate-400">
              Authenticate with your Supabase-backed identity to unlock live
              data.
            </p>
            <div className="mt-4">
              <AuthenticationForm />
            </div>
          </div>
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
            <h2 className="text-lg font-semibold">Account configuration</h2>
            <p className="mt-1 text-xs text-slate-400">
              Maintain notification routing and territory assignments for
              reporting.
            </p>
            <div className="mt-4">
              <AccountConfigurationForm />
            </div>
          </div>
        </section>
      </div>
    </main>
  </>
)
export default HomePage
