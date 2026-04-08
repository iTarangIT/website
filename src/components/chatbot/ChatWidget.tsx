"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageSquare, X, Send, Battery, User } from "lucide-react";
import Image from "next/image";

interface Message {
    role: "user" | "assistant";
    content: string;
}

export default function ChatWidget() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        {
            role: "assistant",
            content: "Hi! 👋 I'm iTarang's AI assistant. Ask me about our batteries, operations, or anything else!",
        },
    ]);
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMessage = input.trim();
        setInput("");
        setMessages((prev) => [...prev, { role: "user", content: userMessage }]);
        setIsLoading(true);

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    messages: [...messages, { role: "user", content: userMessage }],
                }),
            });

            if (!response.ok) throw new Error("API failed");

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            setMessages((prev) => [...prev, { role: "assistant", content: "" }]);

            let done = false;
            while (!done) {
                const { value, done: doneReading } = await reader!.read();
                done = doneReading;
                if (value) {
                    const chunkValue = decoder.decode(value, { stream: true });
                    setMessages((prev) => {
                        const lastMessage = prev[prev.length - 1];
                        return [
                            ...prev.slice(0, -1),
                            { ...lastMessage, content: lastMessage.content + chunkValue },
                        ];
                    });
                }
            }
        } catch (error) {
            console.error(error);
            setMessages((prev) => [...prev, { role: "assistant", content: "Oops! Something went wrong. Please try again or contact us directly." }]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 20, scale: 0.95 }}
                        transition={{ type: "spring", damping: 25, stiffness: 300 }}
                        className="fixed bottom-24 right-4 sm:right-6 z-50 w-[calc(100vw-32px)] sm:w-[400px] h-[500px] bg-white rounded-2xl shadow-2xl border border-gray-100 flex flex-col overflow-hidden"
                    >
                        {/* Header */}
                        <div className="bg-gradient-to-r from-brand-600 to-brand-800 p-4 flex items-center justify-between text-white shadow-md">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded-full flex items-center justify-center overflow-hidden">
                                    <Image src="/images/logo-transparent.png" alt="iTarang" width={32} height={32} className="object-contain w-full h-full rounded-full bg-white p-0.5" />
                                </div>
                                <div>
                                    <h3 className="font-semibold font-sans">iTarang Assistant</h3>
                                    <p className="text-xs text-white/70">Online</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-2 hover:bg-white/10 rounded-full transition-colors"
                                aria-label="Close chat"
                            >
                                <X className="w-5 h-5 text-white" />
                            </button>
                        </div>

                        {/* Messages Area */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/50">
                            {messages.map((msg, idx) => (
                                <div
                                    key={idx}
                                    className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                                >
                                    <div className={`flex gap-2 max-w-[85%] ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                                        <div className={`shrink-0 w-8 h-8 rounded-full flex items-center justify-center overflow-hidden shadow-sm ${msg.role === "user" ? "bg-gray-200" : "bg-white p-0.5"}`}>
                                            {msg.role === "user" ? (
                                                <User className="w-4 h-4 text-gray-500" />
                                            ) : (
                                                <Image src="/images/logo-transparent.png" alt="iTarang" width={32} height={32} className="object-contain w-full h-full rounded-full" />
                                            )}
                                        </div>
                                        <div
                                            className={`p-3 rounded-2xl font-sans text-sm shadow-sm ${msg.role === "user"
                                                ? "bg-brand-600 text-white rounded-tr-none"
                                                : "bg-white text-gray-800 border border-gray-100 rounded-tl-none"
                                                }`}
                                        >
                                            {msg.content}
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className="flex justify-start">
                                    <div className="flex gap-2 max-w-[85%] flex-row">
                                        <div className="shrink-0 w-8 h-8 rounded-full bg-white p-0.5 shadow-sm flex items-center justify-center overflow-hidden">
                                            <Image src="/images/logo-transparent.png" alt="iTarang" width={32} height={32} className="object-contain w-full h-full rounded-full" />
                                        </div>
                                        <div className="p-4 rounded-2xl bg-white border border-gray-100 rounded-tl-none flex items-center gap-1">
                                            <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                            <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                            <div className="w-2 h-2 bg-brand-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                                        </div>
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Area */}
                        <form onSubmit={handleSubmit} className="p-3 bg-white border-t border-gray-100">
                            <div className="relative flex items-center">
                                <input
                                    type="text"
                                    value={input}
                                    onChange={(e) => setInput(e.target.value)}
                                    placeholder="Ask a question..."
                                    className="w-full pl-4 pr-12 py-3 rounded-xl bg-gray-50 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-sans text-sm"
                                    disabled={isLoading}
                                />
                                <button
                                    type="submit"
                                    disabled={!input.trim() || isLoading}
                                    className="absolute right-2 p-2 bg-brand-600 hover:bg-brand-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                                >
                                    <Send className="w-4 h-4" />
                                </button>
                            </div>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Floating Toggle Button */}
            <motion.button
                initial={{ scale: 0, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsOpen((prev) => !prev)}
                className="fixed bottom-24 right-6 z-40 w-14 h-14 bg-gradient-to-tr from-brand-600 to-brand-500 rounded-full flex items-center justify-center text-white shadow-[0_4px_20px_rgba(5,27,154,0.4)] transition-all hover:shadow-[0_6px_25px_rgba(5,27,154,0.5)] focus:outline-none"
                aria-label="Toggle chat"
            >
                {isOpen ? <X className="w-6 h-6" /> : <MessageSquare className="w-6 h-6" />}
            </motion.button>
        </>
    );
}
