import { useEffect, useState } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import AcondicionadorMen from "../assets/CONDITIONER MEN.png";
import ShampooMen from "../assets/SHAMPOO MEN.png";
import crema3en1Men from "../assets/CREAM 3 IN 1.png";
import GelMen from "../assets/GEL MEN.png";
import imageBlack from "../assets/ImagenBlack.png";
import imageBlack2 from "../assets/ImagenBlack2.png";
import logo from "../assets/RFRecurso 1logo men 2.png";
import { useCart } from "./carritoContext";
import { Link, useLocation } from "react-router-dom";

interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  image: string;
  currency?: string;
}

// Función para formatear el precio
const formatPrice = (price: number) => {
  return price.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
};

const DarkCatalog = () => {
  const { addItem } = useCart();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const ref = queryParams.get('ref');

  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchCountry = async () => {
      if (ref) {
        try {
          const response = await fetch(`https://api.unicornio.tech/api/pais?ref=${encodeURIComponent(ref)}`);
          const data = await response.json();
          const country = data.pais;

          // Ajustar precios según el país
          const adjustedProducts = [
            {
              id: 6,
              name: "Acondicionador Men",
              description: "shine & softness",
              price: country === "Colombia" ? 77350 : 507,
              image: AcondicionadorMen,
              currency: country === "Colombia" ? "COP" : "MXN",
            },
            {
              id: 7,
              name: "Shampoo Special Men",
              description: "cleaning & freshness",
              price: country === "Colombia" ? 77350 : 507,
              image: ShampooMen,
              currency: country === "Colombia" ? "COP" : "MXN",
            },
            {
              id: 8,
              name: "Cream 3 in 1 Men",
              description: "repair & define",
              price: country === "Colombia" ? 77350 : 507,
              image: crema3en1Men,
              currency: country === "Colombia" ? "COP" : "MXN",
            },
            {
              id: 9,
              name: "Gel Men",
              description: "shine & hold",
              price: country === "Colombia" ? 59400 : 507,
              image: GelMen,
              currency: country === "Colombia" ? "COP" : "MXN",
            },
          ];

          setProducts(adjustedProducts);
        } catch (error) {
          console.error("Error fetching country:", error);
        } finally {
          setIsLoading(false);
        }
      } else {
        setIsLoading(false);
      }
    };

    fetchCountry();
  }, [ref]);

  const handleAddToCart = (product: Product) => {
    console.log("Agregando al carrito:", product);
    addItem(product);
  };

  return (
    <div className="bg-black min-h-screen text-white">
      {/* Header con logo */}
      <Link to={`/catalog${ref ? `?ref=${ref}` : ''}`} className="block w-full">
        <div className="max-w-screen-xl mx-auto px-4 pt-8">
          <Card className="bg-gray-900 text-white rounded-lg overflow-hidden shadow-md border border-gray-700">
            <div className="flex justify-between items-center p-4 md:p-6">
              <div className="text-center">
                <p className="text-sm md:text-base text-gray-400 uppercase tracking-widest">Linea Special</p>
              </div>
              <div className="flex items-center">
                <img
                  src={logo}
                  alt="Logo"
                  className="w-16 h-16 md:w-20 md:h-20 object-contain"
                />
              </div>
            </div>
          </Card>
        </div>
      </Link>

      {/* Mobile Layout */}
      <div className="md:hidden px-4 space-y-6 pb-24 mt-6">
        {/* Título "Productos" */}
        <h2 className="text-2xl font-bold text-left mb-4" style={{ color: '#BC995A' }}>
          Línea Men
        </h2>

        {/* Primera card */}
        <Card className="bg-white rounded-xl overflow-hidden shadow-md">
          <div className="grid grid-cols-2 gap-4 p-4">
            {products.slice(0, 2).map((product) => (
              <div key={product.id} className="space-y-2 flex flex-col justify-between h-full">
                <img
                  src={product.image}
                  alt={product.name}
                  className="w-full h-40 object-contain mx-auto"
                />
                <h3 className="font-medium text-sm text-center" style={{ color: '#BC995A' }}>{product.name}</h3>
                <p className="text-xs text-center" style={{ color: '#BC995A' }}>{product.description}</p>
                <div className="text-sm font-bold text-center" style={{ color: '#BC995A' }}>
                  {isLoading ? "Cargando..." : `${formatPrice(product.price)} ${product.currency}`}
                </div>
                <Button
                  className="bg-black hover:bg-gray-800 text-white rounded-full px-4 py-1 text-xs w-full"
                  onClick={() => handleAddToCart(product)}
                  disabled={isLoading}
                >
                  Lo quiero
                </Button>
              </div>
            ))}
          </div>
        </Card>

        {/* Resto de productos móviles */}
        <Card className="bg-white rounded-xl overflow-hidden shadow-md">
          <div className="grid grid-cols-2 gap-4">
            <img
              src={imageBlack}
              alt="Lifestyle"
              className="w-full h-full object-cover"
            />
            <div className="p-4 space-y-2 flex flex-col justify-between h-full">
              <img
                src={products[2]?.image}
                alt={products[2]?.name}
                className="w-full h-40 object-contain mx-auto"
              />
              <h3 className="font-medium text-sm text-center" style={{ color: '#BC995A' }}>{products[2]?.name}</h3>
              <p className="text-xs text-center" style={{ color: '#BC995A' }}>{products[2]?.description}</p>
              <div className="text-sm font-bold text-center" style={{ color: '#BC995A' }}>
                {isLoading ? "Cargando..." : `${formatPrice(products[2]?.price)} ${products[2]?.currency}`}
              </div>
              <Button
                className="bg-black hover:bg-gray-800 text-white rounded-full px-4 py-1 text-xs w-full"
                onClick={() => handleAddToCart(products[2])}
                disabled={isLoading}
              >
                Lo quiero
              </Button>
            </div>
          </div>
        </Card>

        <Card className="bg-white rounded-xl overflow-hidden shadow-md">
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 space-y-2 flex flex-col justify-between h-full">
              <img
                src={products[3]?.image}
                alt={products[3]?.name}
                className="w-full h-40 object-contain mx-auto"
              />
              <h3 className="font-medium text-sm text-center" style={{ color: '#BC995A' }}>{products[3]?.name}</h3>
              <p className="text-xs text-center" style={{ color: '#BC995A' }}>{products[3]?.description}</p>
              <div className="text-sm font-bold text-center" style={{ color: '#BC995A' }}>
                {isLoading ? "Cargando..." : `${formatPrice(products[3]?.price)} ${products[3]?.currency}`}
              </div>
              <Button
                className="bg-black hover:bg-gray-800 text-white rounded-full px-4 py-1 text-xs w-full"
                onClick={() => handleAddToCart(products[3])}
                disabled={isLoading}
              >
                Lo quiero
              </Button>
            </div>
            <img
              src={imageBlack2}
              alt="Lifestyle"
              className="w-full h-full object-cover"
            />
          </div>
        </Card>
      </div>

      {/* Desktop Layout */}
      <div className="hidden md:block px-4 pb-16 mt-8">
        {/* Contenedor del grid de productos */}
        <div className="max-w-screen-xl mx-auto">
          {/* Título "Productos" */}
          <h2 className="text-2xl md:text-3xl font-bold text-left mb-6" style={{ color: '#BC995A' }}>
            Linea Men
          </h2>

          {/* Grid de productos */}
          <div className="grid grid-cols-4 gap-6">
            {products.map((product) => (
              <Card key={product.id} className="bg-white rounded-lg overflow-hidden flex flex-col h-full">
                <div className="p-4 flex flex-col items-center justify-between h-full">
                  {/* Imagen */}
                  <div className="w-full h-48 mb-4 flex items-center justify-center">
                    <img
                      src={product.image}
                      alt={product.name}
                      className="w-full h-full object-contain"
                    />
                  </div>

                  {/* Nombre, Descripción y Precio */}
                  <div className="text-center space-y-2 w-full">
                    <h3 className="font-medium text-lg" style={{ color: '#BC995A' }}>{product.name}</h3>
                    <p className="text-sm text-gray-600">{product.description}</p>
                    <div className="text-lg font-bold" style={{ color: '#BC995A' }}>
                      {isLoading ? "Cargando..." : `${formatPrice(product.price)} ${product.currency}`}
                    </div>
                  </div>

                  {/* Botón */}
                  <Button
                    className="w-full bg-black hover:bg-gray-800 text-white rounded-full py-2 text-sm mt-4"
                    onClick={() => handleAddToCart(product)}
                    disabled={isLoading}
                  >
                    Lo quiero
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DarkCatalog;
