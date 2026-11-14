import React from 'react'
import { BrowserRouter, Routes, Route, Navigate, useOutletContext } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RootLayout } from './layouts/RootLayout'
import { DashboardPage } from './pages/DashboardPage'
import { SignalsPage } from './pages/SignalsPage'
import { PositionsPage } from './pages/PositionsPage'
import { OrdersPage } from './pages/OrdersPage'
import { ChannelsPage } from './pages/ChannelsPage'
import { AnalyticsPage } from './pages/AnalyticsPage'
import { SettingsPage } from './pages/SettingsPage'
import { AICopilotPage } from './pages/AICopilotPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 5000,
    },
  },
})

// Helper wrappers to consume outlet context
const DashboardRoute: React.FC = () => {
  const { onOpenSignalModal } = useOutletContext<{ onOpenSignalModal: () => void }>()
  return <DashboardPage onOpenSignalModal={onOpenSignalModal} />
}

const SignalsRoute: React.FC = () => {
  const { onOpenSignalModal } = useOutletContext<{ onOpenSignalModal: () => void }>()
  return <SignalsPage onOpenSignalModal={onOpenSignalModal} />
}

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<RootLayout />}>
            <Route index element={<DashboardRoute />} />
            <Route path="signals" element={<SignalsRoute />} />
            <Route path="copilot" element={<AICopilotPage />} />
            <Route path="positions" element={<PositionsPage />} />
            <Route path="orders" element={<OrdersPage />} />
            <Route path="channels" element={<ChannelsPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
