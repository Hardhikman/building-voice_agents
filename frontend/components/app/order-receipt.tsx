'use client';

import { useEffect, useState } from 'react';
import { useRoomContext } from '@livekit/components-react';
import { motion, AnimatePresence } from 'motion/react';
import { DataPacket_Kind } from 'livekit-client';

interface CoffeeOrder {
    drinkType: string;
    quantity: number;
    size: string;
    milk: string;
    extras: string[];
    name: string;
    timestamp: string;
    orderNumber: string;
}

const MotionDiv = motion.create('div');

export function OrderReceipt() {
    const room = useRoomContext();
    const [order, setOrder] = useState<CoffeeOrder | null>(null);
    const [showReceipt, setShowReceipt] = useState(false);

    useEffect(() => {
        const handleDataReceived = (payload: Uint8Array, participant?: any, kind?: DataPacket_Kind, topic?: string) => {
            console.log('Data received:', { topic, kind, participant });
            if (topic === 'coffee_order') {
                try {
                    const decoder = new TextDecoder();
                    const jsonString = decoder.decode(payload);
                    console.log('Decoded JSON:', jsonString);
                    const data = JSON.parse(jsonString);

                    if (data.type === 'coffee_order' && data.order) {
                        console.log('Setting order:', data.order);
                        setOrder(data.order);
                        setShowReceipt(true);

                        // Auto-hide after 15 seconds
                        setTimeout(() => setShowReceipt(false), 15000);
                    }
                } catch (error) {
                    console.error('Failed to parse order data:', error);
                }
            }
        };

        room.on('dataReceived', handleDataReceived);

        return () => {
            room.off('dataReceived', handleDataReceived);
        };
    }, [room]);

    if (!order) return null;

    return (
        <AnimatePresence>
            {showReceipt && (
                <MotionDiv
                    initial={{ opacity: 0, scale: 0.9, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9, y: 20 }}
                    transition={{ duration: 0.3 }}
                    className="fixed top-4 right-4 z-50 w-80"
                >
                    <div className="bg-background border-input rounded-2xl border p-6 shadow-2xl">
                        {/* Header */}
                        <div className="mb-4 text-center">
                            <h3 className="text-foreground text-xl font-bold">Brew Haven</h3>
                            <p className="text-muted-foreground text-sm">Order Receipt</p>
                        </div>

                        {/* Order Number */}
                        <div className="bg-muted mb-4 rounded-lg p-3 text-center">
                            <p className="text-muted-foreground text-xs uppercase">Order Number</p>
                            <p className="text-foreground font-mono text-lg font-bold">{order.orderNumber}</p>
                        </div>

                        {/* Customer Name */}
                        <div className="mb-4">
                            <p className="text-muted-foreground text-sm">Customer</p>
                            <p className="text-foreground text-lg font-semibold">{order.name}</p>
                        </div>

                        {/* Order Details */}
                        <div className="border-muted space-y-2 border-t border-b py-4">
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">Drink</span>
                                <span className="text-foreground font-medium">
                                    {order.quantity}x {order.drinkType}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">Size</span>
                                <span className="text-foreground font-medium">{order.size}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">Milk</span>
                                <span className="text-foreground font-medium">{order.milk}</span>
                            </div>
                            {order.extras && order.extras.length > 0 && (
                                <div className="flex justify-between">
                                    <span className="text-muted-foreground">Extras</span>
                                    <span className="text-foreground text-right font-medium">
                                        {order.extras.join(', ')}
                                    </span>
                                </div>
                            )}
                        </div>

                        {/* Timestamp */}
                        <div className="mt-4 text-center">
                            <p className="text-muted-foreground text-xs">
                                {new Date(order.timestamp).toLocaleString()}
                            </p>
                        </div>

                        {/* Close Button */}
                        <button
                            onClick={() => setShowReceipt(false)}
                            className="text-muted-foreground hover:text-foreground mt-4 w-full rounded-lg py-2 text-sm transition-colors"
                        >
                            Close
                        </button>
                    </div>
                </MotionDiv>
            )}
        </AnimatePresence>
    );
}
