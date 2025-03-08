"use client"

import { useEffect } from "react"
import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import * as z from "zod"
import { Button } from "./ui/button"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog"
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "./ui/form"
import { Input } from "./ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select"
import { toast } from "../hooks/use-toast"

const formSchema = z.object({
  full_name: z.string().min(2, "El nombre debe tener al menos 2 caracteres"),
  email: z.string().email("Correo electrónico inválido"),
  whatsapp_number: z.string().min(10, "El teléfono debe tener al menos 10 dígitos"),
  distribuidor_id: z.string().min(1, "Debe seleccionar un distribuidor"),
  status: z.enum(["active", "inactive"]),
})

interface Ambassador {
  _id: string
  full_name: string
  email: string
  whatsapp_number: string
  distribuidor_id: string
  status: "active" | "inactive"
  pais: string
}

interface EditAmbassadorModalProps {
  isOpen: boolean
  onClose: () => void
  ambassador: Ambassador
  onUpdate: (ambassador: Ambassador) => void
}

export function EditAmbassadorModal({ isOpen, onClose, ambassador, onUpdate }: EditAmbassadorModalProps) {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      full_name: ambassador.full_name,
      email: ambassador.email,
      whatsapp_number: ambassador.whatsapp_number,
      distribuidor_id: ambassador.distribuidor_id,
      status: ambassador.status,
    },
  })

  // Actualizar valores del formulario cuando cambia el embajador seleccionado
  useEffect(() => {
    form.reset({
      full_name: ambassador.full_name,
      email: ambassador.email,
      whatsapp_number: ambassador.whatsapp_number,
      distribuidor_id: ambassador.distribuidor_id,
      status: ambassador.status,
    })
  }, [ambassador, form])

  // Enviar los cambios al backend
  async function onSubmit(values: z.infer<typeof formSchema>) {
    try {
      const response = await fetch(`https://api.unicornio.tech/embajadores/${ambassador._id}`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(values),
      })

      if (!response.ok) {
        throw new Error("Error al actualizar el embajador")
      }

      const updatedAmbassador = await response.json()
      onUpdate(updatedAmbassador)
      toast({ title: "Éxito", description: "Embajador actualizado correctamente." })
      onClose()
    } catch (error) {
      toast({ title: "Error", description: "No se pudo actualizar el embajador.", variant: "destructive" })
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Editar Embajador</DialogTitle>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Nombre</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Correo Electrónico</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="whatsapp_number"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Teléfono</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="distribuidor_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Distribuidor</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccionar distribuidor" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="distribuidora-central">Distribuidora Central</SelectItem>
                      <SelectItem value="belleza-total">Belleza Total</SelectItem>
                      <SelectItem value="cosmeticos-del-norte">Cosméticos del Norte</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="status"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Estado</FormLabel>
                  <Select onValueChange={field.onChange} value={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Seleccionar estado" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="active">Activo</SelectItem>
                      <SelectItem value="inactive">Inactivo</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="flex justify-end gap-2">
              <Button type="button" variant="outline" onClick={onClose}>
                Cancelar
              </Button>
              <Button type="submit">Guardar Cambios</Button>
            </div>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
