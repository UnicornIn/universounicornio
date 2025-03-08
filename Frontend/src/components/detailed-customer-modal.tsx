"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog"
import { Card, CardContent } from "./ui/card"
import { Badge } from "./ui/badge"

interface Customer {
  id: string
  name?: string
  email?: string
  phone?: string
  ambassadorEmail?: string
  totalOrders: number
  totalSpent: number
}

interface Product {
  title: string
  quantity: number
  unit_price: number
}

interface Order {
  id: string
  date: string
  products: Product[]
  total: number
  status: "completed" | "processing" | "shipped" | "pending"
}

interface DetailedCustomerModalProps {
  isOpen: boolean
  onClose: () => void
  customer: Customer
}

export function DetailedCustomerModal({ isOpen, onClose, customer }: DetailedCustomerModalProps) {
  const [orders, setOrders] = useState<Order[]>([])
  const [loading, setLoading] = useState<boolean>(false)

  const getAccessToken = () => {
    return localStorage.getItem("access_token") || sessionStorage.getItem("access_token") || ""
  }

  useEffect(() => {
    if (!customer?.email) {
      console.error("El cliente no tiene un correo válido")
      return
    }

    const fetchOrders = async () => {
      setLoading(true)
      const accessToken = getAccessToken()

      if (!accessToken) {
        console.error("No se encontró el access_token")
        setLoading(false)
        return
      }

      try {
        const response = await fetch(`https://api.unicornio.tech/orders/${customer.email}`, {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
        })

        if (!response.ok) {
          throw new Error(`Error ${response.status}: No se encontraron pedidos`)
        }

        const data = await response.json()
        console.log("📢 Pedidos obtenidos:", data)

        setOrders(
          data.orders.map((order: any) => ({
            id: order.id,
            date: order.date ? new Date(order.date).toLocaleDateString() : "Fecha no disponible",
            products: order.products || [],
            total: order.total || 0,
            status: order.status || "pending",
          }))
        )
      } catch (error) {
        console.error("Error al cargar pedidos:", error)
        setOrders([])
      } finally {
        setLoading(false)
      }
    }

    fetchOrders()
  }, [customer])

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Detalles del Cliente - {customer.name ?? "Desconocido"}</DialogTitle>
        </DialogHeader>
        <div className="mt-4 space-y-4">
          <div className="grid gap-2">
            <div><span className="font-medium">Email:</span> {customer.email ?? "Sin correo"}</div>
            <div><span className="font-medium">Teléfono:</span> {customer.phone ?? "Sin número"}</div>
            <div><span className="font-medium">Embajador:</span> {customer.ambassadorEmail ?? "No asignado"}</div>
            <div><span className="font-medium">Total de pedidos:</span> {customer.totalOrders}</div>
            <div><span className="font-medium">Total gastado:</span> ${customer.totalSpent.toLocaleString()}</div>
          </div>

          <h3 className="text-lg font-semibold mt-6 mb-2">Historial de Pedidos</h3>

          {loading ? (
            <p>Cargando pedidos...</p>
          ) : orders.length > 0 ? (
            orders.map((order, index) => (
              <Card key={order.id} className="p-4 border rounded-md shadow-sm">
                <CardContent>
                  <div className="flex items-center justify-between">
                    <p className="text-md font-medium">Pedido #{index + 1}</p>
                    <Badge className={`text-white px-3 py-1 rounded-md ${
                      order.status === "completed"
                        ? "bg-green-500"
                        : order.status === "shipped"
                        ? "bg-blue-500"
                        : order.status === "processing"
                        ? "bg-yellow-500"
                        : "bg-gray-500"
                    }`}>
                      {order.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-gray-500">{order.date}</p>

                  {/* ✅ Renderizar correctamente la lista de productos */}
                  <ul className="mt-2 list-disc pl-5 text-sm">
                    {order.products.map((product, idx) => (
                      <li key={idx}>
                        {product.title} - {product.quantity} x ${product.unit_price}
                      </li>
                    ))}
                  </ul>

                  <div className="text-right font-medium text-md mt-3">
                    Total: ${order.total.toLocaleString()}
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <p>Este cliente no tiene pedidos.</p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
