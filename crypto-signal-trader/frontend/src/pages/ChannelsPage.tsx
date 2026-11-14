import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../services/api'
import { Badge } from '../components/common/Badge'
import { Modal } from '../components/common/Modal'
import { formatDate } from '../utils/formatters'
import {
  Send,
  Plus,
  Trash2,
  Eye,
  CheckCircle2,
  XCircle,
  MessageSquare,
  AlertCircle,
  Radio,
} from 'lucide-react'
import type { TelegramChannel, TelegramMessage } from '../types'

export const ChannelsPage: React.FC = () => {
  const queryClient = useQueryClient()
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [channelInput, setChannelInput] = useState('')
  const [addError, setAddError] = useState<string | null>(null)

  // Message drawer
  const [selectedChannel, setSelectedChannel] = useState<TelegramChannel | null>(null)

  const { data: channels = [], isLoading } = useQuery({
    queryKey: ['channels'],
    queryFn: () => api.getChannels(),
    refetchInterval: 5000,
  })

  const { data: channelMessages = [], isLoading: isLoadingMessages } = useQuery({
    queryKey: ['channelMessages', selectedChannel?.id],
    queryFn: () => (selectedChannel ? api.getChannelMessages(selectedChannel.id, 50) : []),
    enabled: !!selectedChannel,
    refetchInterval: selectedChannel ? 4000 : false,
  })

  const addChannelMutation = useMutation({
    mutationFn: (identifier: string) => api.addChannel(identifier),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      setIsAddModalOpen(false)
      setChannelInput('')
      setAddError(null)
    },
    onError: (err: any) => {
      setAddError(err.message || 'Failed to add channel')
    },
  })

  const toggleChannelMutation = useMutation({
    mutationFn: ({ id, is_monitored }: { id: string; is_monitored: boolean }) =>
      api.updateChannel(id, { is_monitored }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
    },
  })

  const deleteChannelMutation = useMutation({
    mutationFn: (id: string) => api.deleteChannel(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] })
      if (selectedChannel) setSelectedChannel(null)
    },
  })

  const handleAddSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!channelInput.trim()) return
    addChannelMutation.mutate(channelInput.trim())
  }

  const handleDelete = (channel: TelegramChannel) => {
    if (confirm(`Remove @${channel.channel_username || channel.channel_id} from monitored list?`)) {
      deleteChannelMutation.mutate(channel.id)
    }
  }

  return (
    <div className="p-4 lg:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl lg:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            Telegram Channels
            <span className="text-xs font-mono text-gray-400 bg-navy-800 px-2.5 py-1 rounded-md border border-white/[0.04]">
              {channels.length} Monitored
            </span>
          </h1>
          <p className="text-xs text-gray-400 mt-1">
            Authorize and monitor crypto broadcast channels for real-time trade signals.
          </p>
        </div>

        <button
          onClick={() => {
            setAddError(null)
            setIsAddModalOpen(true)
          }}
          className="btn-primary text-xs flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          <span>Add Channel</span>
        </button>
      </div>

      {/* Channel Cards Grid */}
      {isLoading ? (
        <div className="card p-8 text-center text-gray-500 text-xs">Loading channel configurations...</div>
      ) : channels.length === 0 ? (
        <div className="card p-12 text-center text-gray-500 text-xs space-y-3">
          <Send className="w-8 h-8 text-gray-600 mx-auto" />
          <p>No Telegram channels are currently configured for monitoring.</p>
          <button
            onClick={() => setIsAddModalOpen(true)}
            className="btn-primary text-xs inline-flex items-center gap-2"
          >
            <Plus className="w-4 h-4" />
            Add First Channel
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {channels.map((chan) => (
            <div
              key={chan.id}
              className="card p-5 space-y-4 hover:border-blue-500/20 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <div className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      <Send className="w-4 h-4" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white tracking-tight">
                        {chan.channel_title || `@${chan.channel_username || chan.channel_id}`}
                      </h4>
                      <p className="text-[11px] text-gray-400 font-mono">
                        {chan.channel_username ? `@${chan.channel_username}` : `ID: ${chan.channel_id}`}
                      </p>
                    </div>
                  </div>

                  <Badge variant={chan.is_monitored ? 'connected' : 'default'}>
                    {chan.is_monitored ? 'MONITORED' : 'PAUSED'}
                  </Badge>
                </div>

                {/* Counters */}
                <div className="grid grid-cols-3 gap-2 mt-4 p-2.5 rounded-xl bg-navy-800/60 border border-white/[0.04] text-center">
                  <div>
                    <span className="text-[10px] text-gray-400 uppercase">Received</span>
                    <div className="font-mono text-sm font-bold text-white mt-0.5">
                      {chan.messages_received}
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-gray-400 uppercase">Processed</span>
                    <div className="font-mono text-sm font-bold text-blue-400 mt-0.5">
                      {chan.messages_processed}
                    </div>
                  </div>
                  <div>
                    <span className="text-[10px] text-gray-400 uppercase">Signals</span>
                    <div className="font-mono text-sm font-bold text-emerald-400 mt-0.5">
                      {chan.signals_parsed}
                    </div>
                  </div>
                </div>

                {chan.last_error && (
                  <div className="mt-3 p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[10px] flex items-center gap-1.5 font-mono">
                    <AlertCircle className="w-3 h-3 shrink-0" />
                    <span className="truncate">{chan.last_error}</span>
                  </div>
                )}
              </div>

              {/* Action buttons */}
              <div className="pt-3 border-t border-white/[0.06] flex items-center justify-between text-xs">
                <button
                  onClick={() => setSelectedChannel(chan)}
                  className="text-gray-400 hover:text-white flex items-center gap-1.5 transition-colors"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>View Messages</span>
                </button>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() =>
                      toggleChannelMutation.mutate({
                        id: chan.id,
                        is_monitored: !chan.is_monitored,
                      })
                    }
                    className="btn-ghost text-[11px] py-1 px-2.5"
                  >
                    {chan.is_monitored ? 'Pause' : 'Resume'}
                  </button>

                  <button
                    onClick={() => handleDelete(chan)}
                    className="p-1.5 rounded-lg text-rose-400 hover:bg-rose-500/10 transition-colors"
                    title="Delete channel"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Channel Modal */}
      <Modal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        title="Add Telegram Channel"
      >
        <form onSubmit={handleAddSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-400 mb-1">
              Channel Username or ID
            </label>
            <input
              type="text"
              required
              value={channelInput}
              onChange={(e) => setChannelInput(e.target.value)}
              placeholder="e.g. @binance_signals or -100192837482"
              className="input font-mono"
            />
            <p className="text-[11px] text-gray-500 mt-1.5">
              Enter the public @handle or numeric Telegram chat ID. Your Telethon client will resolve and begin listening.
            </p>
          </div>

          {addError && (
            <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{addError}</span>
            </div>
          )}

          <div className="pt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={() => setIsAddModalOpen(false)}
              className="btn-ghost text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={addChannelMutation.isPending}
              className="btn-primary text-xs"
            >
              {addChannelMutation.isPending ? 'Verifying...' : 'Add Channel'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Messages Drawer / Modal */}
      <Modal
        isOpen={!!selectedChannel}
        onClose={() => setSelectedChannel(null)}
        title={`Message Stream — ${selectedChannel?.channel_title || selectedChannel?.channel_username || ''}`}
        maxWidth="lg"
      >
        <div className="space-y-3">
          {isLoadingMessages ? (
            <div className="p-8 text-center text-gray-500 text-xs">Loading channel messages...</div>
          ) : channelMessages.length === 0 ? (
            <div className="p-8 text-center text-gray-500 text-xs">
              No messages recorded for this channel yet.
            </div>
          ) : (
            <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
              {channelMessages.map((msg) => (
                <div
                  key={msg.id}
                  className="p-3 rounded-xl bg-navy-800/80 border border-white/[0.04] text-xs space-y-1.5"
                >
                  <div className="flex items-center justify-between text-[11px] text-gray-400">
                    <span className="font-mono">Msg #{msg.message_id}</span>
                    <span>{formatDate(msg.created_at)}</span>
                  </div>

                  <pre className="p-2 bg-navy-900 rounded font-mono text-[11px] text-gray-200 whitespace-pre-wrap">
                    {msg.raw_text}
                  </pre>

                  <div className="flex items-center gap-2 pt-1 text-[11px]">
                    {msg.signal_parsed ? (
                      <span className="text-emerald-400 flex items-center gap-1 font-mono">
                        <CheckCircle2 className="w-3 h-3" />
                        Valid signal parsed
                      </span>
                    ) : (
                      <span className="text-gray-500 font-mono">
                        {msg.parse_error ? `Rejected: ${msg.parse_error}` : 'Non-signal message'}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="pt-2 flex justify-end">
            <button
              type="button"
              onClick={() => setSelectedChannel(null)}
              className="btn-ghost text-xs"
            >
              Close
            </button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
