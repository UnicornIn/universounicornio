import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { Edit, Trash2, ShoppingBag } from "lucide-react"
import { EditAmbassadorModal } from "./edit-ambassador-modal"
import { AmbassadorDetailsModal } from "./ambassador-details-modal"

interface Ambassador {
  _id: string // Cambié de `number` a `string` aquí también
  full_name: string
  email: string
  whatsapp_number: string
  distribuidor_id: string
  status: "active" | "inactive"
  pais: string
}

export function AmbassadorList() {
  const [ambassadors, setAmbassadors] = useState<Ambassador[]>([])
  const [selectedAmbassador, setSelectedAmbassador] = useState<Ambassador | null>(null)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false)
  const [loading, setLoading] = useState(true)

  // 🔹 Obtener embajadores desde el backend
  useEffect(() => {
    const fetchAmbassadors = async () => {
      try {
        const response = await fetch("https://api.unicornio.tech/embajadores", {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
            "Content-Type": "application/json",
          },
        })
        if (!response.ok) {
          throw new Error("No se pudieron obtener los embajadores")
        }
        const data = await response.json()
        setAmbassadors(data)
      } catch (error) {
        console.error(error)
      } finally {
        setLoading(false)
      }
    }

    fetchAmbassadors()
  }, [])

  // 🔹 Eliminar embajador
  const handleDelete = async (id: string) => {
    if (confirm("¿Estás seguro de que deseas eliminar este embajador?")) {
      try {
        const response = await fetch(`https://api.unicornio.tech/embajadores/${id}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          },
        })
        if (!response.ok) {
          throw new Error("Error al eliminar embajador")
        }
        setAmbassadors(ambassadors.filter((a) => a._id !== id))
      } catch (error) {
        console.error(error)
      }
    }
  }

  // 🔹 Actualizar embajador
  const handleUpdate = (updatedAmbassador: Ambassador) => {
    setAmbassadors(ambassadors.map((a) => (a._id === updatedAmbassador._id ? updatedAmbassador : a)))
    setIsEditModalOpen(false)
  }

  if (loading) {
    return <p>Cargando embajadores...</p>
  }

  return (
    <div className="grid gap-4">
      {ambassadors.length === 0 ? (
        <p>No hay embajadores disponibles.</p>
      ) : (
        ambassadors.map((ambassador) => (
          <Card key={ambassador._id}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-xl">{ambassador.full_name}</CardTitle>
              <div className="flex items-center gap-2">
                <Badge variant={ambassador.status === "active" ? "default" : "secondary"}>
                  {ambassador.status === "active" ? "Activo" : "Inactivo"}
                </Badge>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    setSelectedAmbassador(ambassador)
                    setIsDetailsModalOpen(true)
                  }}
                >
                  <ShoppingBag className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => {
                    setSelectedAmbassador(ambassador)
                    setIsEditModalOpen(true)
                  }}
                >
                  <Edit className="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" onClick={() => handleDelete(ambassador._id)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">Email:</span>
                  <span>{ambassador.email}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">Teléfono:</span>
                  <span>{ambassador.whatsapp_number}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">País:</span>
                  <span>{ambassador.pais}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))
      )}

      {selectedAmbassador && (
        <>
          <EditAmbassadorModal
            isOpen={isEditModalOpen}
            onClose={() => setIsEditModalOpen(false)}
            ambassador={selectedAmbassador}
            onUpdate={handleUpdate}
          />
          <AmbassadorDetailsModal
            isOpen={isDetailsModalOpen}
            onClose={() => setIsDetailsModalOpen(false)}
            ambassador={{
              id: selectedAmbassador._id, // Aseguramos que se pase el `_id` como string
              name: selectedAmbassador.full_name,
              phone: selectedAmbassador.whatsapp_number,
              distributor: selectedAmbassador.distribuidor_id,
              salesCount: 0, // Ajusta este valor si tienes los datos correctos
              email: selectedAmbassador.email, // Aseguramos que también se pase el email
              status: selectedAmbassador.status, // Aseguramos que también se pase el status
            }}
          />
        </>
      )}
    </div>
  )
}
