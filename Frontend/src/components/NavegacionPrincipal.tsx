import { Link, useLocation } from 'react-router-dom';
import { Home, Wallet, BookOpen, Package, Users, User, ShoppingCart, LogOut, Store, Award, UserPlus} from 'lucide-react';

interface NavegacionPrincipalProps {
  onLogout: () => void;
}

const NavegacionPrincipal: React.FC<NavegacionPrincipalProps> = ({ onLogout }) => {
  const location = useLocation();
  const rol = localStorage.getItem('rol') || '';
  const nombreNegocio = localStorage.getItem('nombre') || 'Nombre del Negocio';

  // Función para manejar el cierre de sesión
  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('pais');
    localStorage.removeItem('rol');
    localStorage.removeItem('cart');
    localStorage.removeItem('nombre');
    localStorage.removeItem('negocio');
    localStorage.removeItem('profileData');
    localStorage.removeItem('orders'); // Eliminar pedidos almacenados
    onLogout();
};


  // Filtrar los elementos de navegación según el rol del usuario
  const navItems = [
    { name: 'Panel', href: '/', icon: Home },
    ...(rol !== 'Negocio' && rol !== 'Distribuidor' ? [{ name: 'Billetera', href: '/wallet', icon: Wallet }] : []), // Oculta "Billetera" si es "Negocio" o "Distribuidor"
    { name: 'Aprendizaje', href: '/learning', icon: BookOpen },
    { name: 'Productos', href: '/products', icon: Package },
    ...(rol !== 'Negocio' && rol !== 'Distribuidor' ? [{ name: 'Clientes', href: '/clients', icon: Users }] : []), // Oculta "Clientes" si es "Negocio" o "Distribuidor"
    ...(rol !== 'Embajador' ? [{ name: "Clientes Detallados", href: "/detailed-customers", icon: UserPlus }] : []), // Oculta "Clientes Detallados" si es "Embajador"
    { name: 'Pedidos', href: '/orders', icon: ShoppingCart },
    ...(rol !== 'Distribuidor' && rol !== 'Embajador' ? [{ name: "Distribuidores", href: "/distributors", icon: Store }] : []), // Oculta "Distribuidores" si es "Distribuidor" o "Embajador"
    ...(rol === 'Distribuidor' ? [{ name: "Embajadores", href: "/ambassadors", icon: Award }] : []), // Muestra "Embajadores" solo si es "Distribuidor"
    { name: 'Perfil', href: '/profile', icon: User },
  ];

  return (
    <>
      {/* Navegación inferior móvil */}
      <nav className="fixed bottom-0 left-0 z-50 w-full border-t border-gray-200 bg-white md:hidden">
        <div className="mx-auto grid max-w-screen-xl grid-cols-7 gap-2 px-2 py-3">
          {navItems.map((item) => (
            <Link
              key={item.name}
              to={item.href}
              className={`flex flex-col items-center py-2 ${
                location.pathname === item.href ? 'text-blue-600' : 'text-gray-500 hover:text-blue-600'
              }`}
            >
              <item.icon className="h-6 w-6 mb-1" />
              <span className="text-xs font-medium truncate w-full text-center">{item.name}</span>
            </Link>
          ))}
        </div>
      </nav>

      {/* Navegación lateral de escritorio */}
      <div className="hidden w-64 flex-shrink-0 border-r border-gray-200 bg-white md:block">
        <div className="flex h-full flex-col">
          <div className="flex h-16 flex-shrink-0 items-center px-4">
            <h1 className="text-xl font-bold truncate whitespace-nowrap">
              {rol === 'Negocio' 
                ? nombreNegocio 
                : rol === 'Distribuidor' 
                  ? 'Distribuidor' 
                  : 'Embajador de la Marca'
              }
            </h1>
          </div>
          <div className="flex flex-1 flex-col overflow-y-auto">
            <nav className="flex-1 space-y-1 px-4 py-4">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`group flex items-center gap-3 rounded-md px-3 py-3 text-sm font-medium ${
                    location.pathname === item.href
                      ? 'bg-gray-100 text-gray-900'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
                >
                  <item.icon
                    className={`h-6 w-6 flex-shrink-0 ${
                      location.pathname === item.href ? 'text-gray-500' : 'text-gray-400 group-hover:text-gray-500'
                    }`}
                  />
                  {item.name}
                </Link>
              ))}
              <button
                onClick={handleLogout}
                className="group flex w-full items-center gap-3 rounded-md px-3 py-3 text-sm font-medium text-gray-600 hover:bg-gray-50 hover:text-gray-900 text-left"
              >
                <LogOut className="h-6 w-6 flex-shrink-0 text-gray-400 group-hover:text-gray-500" />
                Cerrar sesión
              </button>
            </nav>
          </div>
        </div>
      </div>
    </>
  );
};

export default NavegacionPrincipal;