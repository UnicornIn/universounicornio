import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Checkbox } from "./ui/checkbox";
import { Button } from "./ui/button";
import { ContactDetails } from "./contact-details";

interface Purchase {
  id: number;
  product: string;
  productName: string;
  date: string;
  amount: number;
}

interface Contact {
  id: number;
  name: string;
  email: string;
  whatsapp_phone: string;
  instagram?: string;
  whatsapp?: string;
  purchaseHistory: Purchase[];
}

export function ContactList() {
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selectedContacts, setSelectedContacts] = useState<number[]>([]);
  const [selectedContact, setSelectedContact] = useState<Contact | null>(null);

  const token = localStorage.getItem("access_token");

  useEffect(() => {
    const storedContacts = localStorage.getItem("clients");

    if (storedContacts) {
      setContacts(JSON.parse(storedContacts));
      console.log("📂 Clientes cargados desde localStorage");
      return;
    }

    const fetchContacts = async () => {
      if (!token) {
        console.error("No se encontró el token de acceso");
        return;
      }

      try {
        const response = await fetch("https://api.unicornio.tech/clients", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          const transformedContacts: Contact[] = data.map((contact: any) => ({
            id: Number(contact.client_id),
            name: contact.name,
            email: contact.email,
            whatsapp_phone: contact.whatsapp_phone,
            instagram: contact.instagram || "",
            whatsapp: contact.whatsapp || contact.whatsapp_phone,
            purchaseHistory: contact.purchaseHistory || [],
          }));

          setContacts(transformedContacts);
          localStorage.setItem("clients", JSON.stringify(transformedContacts)); // Guardar en localStorage
          console.log("✅ Clientes guardados en localStorage");
        } else {
          console.error("Error al obtener los contactos");
        }
      } catch (error) {
        console.error("Error de red:", error);
      }
    };

    fetchContacts();
  }, [token]);

  const handleCheckboxChange = (contactId: number) => {
    setSelectedContacts((prev) =>
      prev.includes(contactId)
        ? prev.filter((id) => id !== contactId)
        : [...prev, contactId]
    );
  };

  const handleViewDetails = (contact: Contact) => {
    setSelectedContact(contact);
  };

  return (
    <div className="mt-8 grid gap-8 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Contactos</CardTitle>
        </CardHeader>
        <CardContent>
          {contacts.length === 0 ? (
            <p className="text-gray-500">No hay clientes disponibles.</p>
          ) : (
            <ul className="space-y-4">
              {contacts.map((contact) => (
                <li key={contact.id} className="flex items-center justify-between space-x-4">
                  <div className="flex items-center space-x-4">
                    <Checkbox
                      id={`contact-${contact.id}`}
                      checked={selectedContacts.includes(contact.id)}
                      onCheckedChange={() => handleCheckboxChange(contact.id)}
                    />
                    <label
                      htmlFor={`contact-${contact.id}`}
                      className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      {contact.name}
                    </label>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => handleViewDetails(contact)}>
                    Ver Detalles
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
      {selectedContact && (
        <ContactDetails contact={selectedContact} onClose={() => setSelectedContact(null)} />
      )}
    </div>
  );
}
