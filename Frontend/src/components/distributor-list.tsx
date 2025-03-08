"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card"
import { Button } from "./ui/button"
import { Badge } from "./ui/badge"
import { Edit, Trash2, Users } from "lucide-react"
import { EditDistributorModal } from "./edit-distributor-modal"
import { DistributorDetailsModal } from "./distributor-details-modal"
import { Distributor } from "./types"

export function DistributorList() {
  const [distributors, setDistributors] = useState<Distributor[]>([])
  const [selectedDistributor, setSelectedDistributor] = useState<Distributor | null>(null)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false)

  // Obtener los distribuidores desde el backend
  const fetchDistributors = async () => {
    const token = localStorage.getItem("access_token") // Corregido el nombre del token

    if (!token) {
      console.error("No se encontró el token de autenticación.")
      return
    }

    try {
      const response = await fetch("https://api.unicornio.tech/distribuidores/negocio/", {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) throw new Error("Error al obtener los distribuidores")

      const data = await response.json()

      // Transformar datos si el backend usa nombres en español
      const transformedData = data.map((dist: any) => ({
        id: dist.id,
        name: dist.nombre,
        phone: dist.telefono,
        email: dist.correo_electronico,
        location: dist.pais,
        ambassadorsCount: 0, // Valor predeterminado si no viene de la API
      }))

      setDistributors(transformedData)
    } catch (error) {
      console.error("Error:", error)
    }
  }

  useEffect(() => {
    fetchDistributors()
  }, [])

  const handleDelete = async (id: string) => {
    if (!confirm("¿Estás seguro de que deseas eliminar este distribuidor?")) return

    const token = localStorage.getItem("access_token") // Corregido el nombre del token

    try {
      const response = await fetch(`https://api.unicornio.tech/distribuidores/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      })

      if (!response.ok) throw new Error("Error al eliminar el distribuidor")

      setDistributors(distributors.filter((d) => d.id !== id)) // Actualizar estado
    } catch (error) {
      console.error("Error:", error)
    }
  }

  const handleUpdate = async (updatedDistributor: Distributor) => {
    const token = localStorage.getItem("access_token") // Corregido el nombre del token

    try {
      const response = await fetch(`https://api.unicornio.tech/distribuidores/${updatedDistributor.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(updatedDistributor),
      })

      if (!response.ok) throw new Error("Error al actualizar el distribuidor")

      setDistributors(distributors.map((d) => (d.id === updatedDistributor.id ? updatedDistributor : d)))
      setIsEditModalOpen(false)
    } catch (error) {
      console.error("Error:", error)
    }
  }

  return (
    <div className="grid gap-4">
      {distributors.map((distributor) => (
        <Card key={distributor.id}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-xl">{distributor.name}</CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="default">Activo</Badge> {/* No se usa "status", puedes quitarlo si no lo necesitas */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  setSelectedDistributor(distributor)
                  setIsDetailsModalOpen(true)
                }}
              >
                <Users className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => {
                  setSelectedDistributor(distributor)
                  setIsEditModalOpen(true)
                }}
              >
                <Edit className="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" onClick={() => handleDelete(distributor.id)}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-2">
              <div className="flex items-center gap-2">
                <span className="font-medium">Ubicación:</span>
                <span>{distributor.location}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">Embajadores:</span>
                <span>{distributor.ambassadorsCount}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-medium">Contacto:</span>
                <span>
                  {distributor.phone} | {distributor.email}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      {selectedDistributor && (
        <>
          <EditDistributorModal
            isOpen={isEditModalOpen}
            onClose={() => setIsEditModalOpen(false)}
            distributor={selectedDistributor}
            onUpdate={handleUpdate}
          />
          <DistributorDetailsModal
            isOpen={isDetailsModalOpen}
            onClose={() => setIsDetailsModalOpen(false)}
            distributor={selectedDistributor}
          />
        </>
      )}
    </div>
  )
}
