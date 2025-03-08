"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"
import { Badge } from "./ui/badge"
import { Button } from "./ui/button"
import { Eye } from "lucide-react"
import { DetailedCustomerModal } from "./detailed-customer-modal"

// Definición de la interfaz para los clientes
interface Customer {
  id: string
  name: string
  email: string
  phone: string
  ambassadorEmail: string
  totalOrders: number
  totalSpent: number
}

interface CustomerListProps {
  searchTerm: string
}

export function CustomerList({ searchTerm }: CustomerListProps) {
  const [customers, setCustomers] = useState<Customer[]>([])
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null)

  // Obtener el access_token de localStorage o sessionStorage
  const getAccessToken = () => {
    return localStorage.getItem("access_token") || sessionStorage.getItem("access_token") || ""
  }

  useEffect(() => {
    const fetchCustomers = async () => {
      const accessToken = getAccessToken()
      if (!accessToken) {
        console.error("❌ No se encontró el access_token")
        return
      }
  
      try {
        const response = await fetch("https://api.unicornio.tech/clients-orders", {
          method: "GET",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
          },
        })
  
        if (!response.ok) {
          throw new Error(`❌ Error ${response.status}: No se pudieron obtener los clientes`)
        }
  
        const data = await response.json()
        console.log("📢 Respuesta de la API:", data)

        const formattedCustomers: Customer[] = data.clients.map((client: any) => ({
          id: client.id,  // ✅ Corregido: `client.id` en lugar de `client._id`
          name: client.nombre || "Desconocido",
          email: client.correo_electronico || "Sin correo",
          phone: client.telefono || "Sin número",
          ambassadorEmail: client.ref || "No asignado",
          totalOrders: client.total_orders ?? 0,
          totalSpent: client.total_spent ?? 0,
        }))
        
        console.log("📢 Clientes procesados:", formattedCustomers)
        setCustomers(formattedCustomers)
      } catch (error) {
        console.error("❌ Error al cargar clientes:", error)
      }
    }
  
    fetchCustomers()
  }, [])

  // Filtrar clientes según el término de búsqueda
  const filteredCustomers = customers.filter(
    (customer) =>
      customer.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      customer.email.toLowerCase().includes(searchTerm.toLowerCase())
  )

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {filteredCustomers.map((customer) => (
        <Card key={customer.id} className="overflow-hidden">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center justify-between">
              <span className="text-lg font-semibold">{customer.name}</span>
              <Button variant="ghost" size="icon" onClick={() => setSelectedCustomer(customer)}>
                <Eye className="h-4 w-4" />
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-1">
              <div className="text-sm text-muted-foreground">{customer.email}</div>
              <div className="text-sm text-muted-foreground">{customer.phone}</div>
              <div className="mt-2 flex items-center justify-between">
                <Badge variant="secondary">{customer.totalOrders} pedidos</Badge>
                <span className="text-sm font-medium">Total: ${customer.totalSpent.toFixed(2)}</span>
              </div>
              <div className="mt-2 text-xs text-muted-foreground">Embajador: {customer.ambassadorEmail}</div>
            </div>
          </CardContent>
        </Card>
      ))}
      
      {/* Modal de detalles del cliente */}
      {selectedCustomer && (
        <DetailedCustomerModal
          customer={selectedCustomer}
          isOpen={!!selectedCustomer}
          onClose={() => setSelectedCustomer(null)}
        />
      )}
    </div>
  )
}
