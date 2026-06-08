import mongoose from 'mongoose'

const chatLogSchema = mongoose.Schema(
  {
    userId: {
      type: mongoose.Schema.Types.ObjectId,
      required: true,
      ref: 'User',
    },
    userName: { type: String, default: '' },
    message: { type: String, required: true },
    piiEntities: [{ type: String }],
    route: {
      type: String,
      enum: ['local', 'cloud'],
      required: true,
    },
    model: { type: String, required: true },
    reply: { type: String, default: '' },
    latencyMs: { type: Number, default: 0 },
    costUsd: { type: Number, default: 0 },
  },
  {
    timestamps: true,
  }
)

const ChatLog = mongoose.model('ChatLog', chatLogSchema)

export default ChatLog
