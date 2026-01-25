// src/components/ChatBot/ChatBot.jsx
import React, { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Zap, Loader2 } from "lucide-react";
import { sendChatMessage, checkChatbotHealth } from "../../api/chatbot";
import "./ChatBot.css";

const ChatBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "👋 Hi! I'm your P2P Energy Trading assistant. I can help you:\n\n• Register participants on the blockchain\n• Submit buy/sell orders\n• Check trading phase & round\n• Advance phases\n• View participants\n\nWhat would you like to do?",
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isConfigured, setIsConfigured] = useState(true);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Check chatbot health on mount
  useEffect(() => {
    checkChatbotHealth().then((result) => {
      if (result.status !== "ok") {
        setIsConfigured(false);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `⚠️ **Chatbot not configured**: ${result.message}\n\nTo enable AI features, add \`GEMINI_API_KEY=your_key\` to your \`.env\` file in the api folder.`,
          },
        ]);
      }
    });
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = { role: "user", content: input.trim() };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const allMessages = [...messages, userMessage];
      const result = await sendChatMessage(allMessages);
      
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: result.response },
      ]);
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `❌ Error: ${error.message}\n\nPlease try again or check if the API server is running.`,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatMessage = (content) => {
    // Simple markdown-like formatting
    return content
      .split("\n")
      .map((line, i) => {
        // Bold text
        line = line.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
        // Code blocks
        line = line.replace(/`(.*?)`/g, "<code>$1</code>");
        // Bullet points
        if (line.startsWith("• ") || line.startsWith("- ")) {
          return `<li key="${i}">${line.substring(2)}</li>`;
        }
        return line;
      })
      .join("<br/>");
  };

  return (
    <>
      {/* Floating Button */}
      <button
        className={`chatbot-fab ${isOpen ? "hidden" : ""}`}
        onClick={() => setIsOpen(true)}
        aria-label="Open AI Assistant"
      >
        <Zap className="fab-icon" />
        <span className="fab-pulse"></span>
      </button>

      {/* Chat Window */}
      <div className={`chatbot-window ${isOpen ? "open" : ""}`}>
        {/* Header */}
        <div className="chatbot-header">
          <div className="header-info">
            <div className="header-avatar">
              <Zap size={20} />
            </div>
            <div>
              <h3>Energy Trading AI</h3>
              <span className={`status ${isConfigured ? "online" : "offline"}`}>
                {isConfigured ? "Online" : "Not Configured"}
              </span>
            </div>
          </div>
          <button className="close-btn" onClick={() => setIsOpen(false)}>
            <X size={20} />
          </button>
        </div>

        {/* Messages */}
        <div className="chatbot-messages">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              {msg.role === "assistant" && (
                <div className="avatar">
                  <Zap size={14} />
                </div>
              )}
              <div
                className="message-content"
                dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }}
              />
            </div>
          ))}
          {isLoading && (
            <div className="message assistant">
              <div className="avatar">
                <Zap size={14} />
              </div>
              <div className="message-content typing">
                <Loader2 className="spin" size={16} />
                <span>Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chatbot-input">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Ask about energy trading..."
            rows={1}
            disabled={isLoading}
            textColor="black"
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
          >
            {isLoading ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
          </button>
        </div>

        {/* Quick Actions */}
        <div className="quick-actions">
          {[
            "Show available Pis",
            "Current phase?",
            "List participants",
          ].map((action) => (
            <button
              key={action}
              className="quick-btn"
              onClick={() => {
                setInput(action);
                setTimeout(() => handleSend(), 100);
              }}
              disabled={isLoading}
            >
              {action}
            </button>
          ))}
        </div>
      </div>
    </>
  );
};

export default ChatBot;

