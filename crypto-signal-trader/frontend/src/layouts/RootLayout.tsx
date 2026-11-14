import React, { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Navbar } from '../components/common/Navbar'
import { Sidebar } from '../components/common/Sidebar'
import { PaperTradingBanner } from '../components/common/PaperTradingBanner'
import { QuickSignalModal } from '../components/dashboard/QuickSignalModal'
import { useWebSocket } from '../hooks/useWebSocket'

export const RootLayout: React.FC = () => {
  const [isSignalModalOpen, setIsSignalModalOpen] = useState(false)

  // Listen to background WebSocket updates
  useWebSocket()

  return (
    <div className="min-h-screen bg-navy-900 flex flex-col text-white selection:bg-blue-500/30">
      {/* Top Navigation */}
      <Navbar onOpenSignalModal={() => setIsSignalModalOpen(true)} />

      {/* Persistent Safety Banner */}
      <PaperTradingBanner />

      {/* Main Terminal Shell */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <Sidebar className="hidden md:flex" />

        {/* Dynamic Route Content */}
        <main className="flex-1 overflow-y-auto min-h-[calc(100vh-6.5rem)]">
          <Outlet context={{ onOpenSignalModal: () => setIsSignalModalOpen(true) }} />
        </main>
      </div>

      {/* Signal Simulation Dialog */}
      <QuickSignalModal
        isOpen={isSignalModalOpen}
        onClose={() => setIsSignalModalOpen(false)}
      />
    </div>
  )
}
