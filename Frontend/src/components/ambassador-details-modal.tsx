import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./ui/dialog"
import { Card, CardContent } from "./ui/card"
import { Badge } from "./ui/badge"

interface Sale {
  id: number
  date: string
  product: string
  amount: number
}

interface Ambassador {
  id: string // Cambié de `number` a `string`
  name: string
  email: string
  phone: string
  distributor: string
  salesCount: number
  status: "active" | "inactive"
}

// Datos de ejemplo de ventas
const mockSales: Sale[] = [
  {
    id: 1,
    date: "2023-06-15",
    product: "Champú Definidor de Rizos",
    amount: 18.99,
  },
  {
    id: 2,
    date: "2023-06-18",
    product: "Acondicionador Hidratante",
    amount: 20.99,
  },
  {
    id: 3,
    date: "2023-06-20",
    product: "Gel Potenciador de Rizos",
    amount: 16.99,
  },
]

interface AmbassadorDetailsModalProps {
  isOpen: boolean
  onClose: () => void
  ambassador: Ambassador
}

export function AmbassadorDetailsModal({ isOpen, onClose, ambassador }: AmbassadorDetailsModalProps) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Detalles de Ventas - {ambassador.name}</DialogTitle>
        </DialogHeader>
        <div className="mt-4 space-y-4">
          {mockSales.map((sale) => (
            <Card key={sale.id}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">{sale.product}</h3>
                    <p className="text-sm text-muted-foreground">{sale.date}</p>
                  </div>
                  <Badge variant="secondary">${sale.amount.toFixed(2)}</Badge>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}
