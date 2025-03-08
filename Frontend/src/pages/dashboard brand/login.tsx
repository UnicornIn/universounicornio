import { useState } from 'react';
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "../../components/ui/card";

interface LoginFormProps {
  onLogin?: (token: string, pais: string) => void;
}

export default function LoginForm({ onLogin }: LoginFormProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [showRedirectMessage, setShowRedirectMessage] = useState(false);
  const [correctUrl, setCorrectUrl] = useState('');

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
  
    // Convertir el email a minúsculas antes de enviarlo
    const lowerCaseEmail = email.toLowerCase(); // <-- Esta es la única línea añadida
  
    console.log('Iniciando sesión con:', { email: lowerCaseEmail, password });
  
    try {
      const formData = new FormData();
      formData.append('username', lowerCaseEmail);  // Usar el email en minúsculas
      formData.append('password', password);
  
      const response = await fetch('https://api.unicornio.tech/token', {
        method: 'POST',
        body: formData,
      });
  
      if (!response.ok) {
        const data = await response.json();
        setErrorMessage(data.detail || 'Error al iniciar sesión');
        return;
      }
  
      const data = await response.json();
  
      // Guardar token y país en el localStorage
      const token = data.access_token;
      const decodedToken = JSON.parse(atob(token.split('.')[1])); // Decodificar el token JWT
      const pais = decodedToken.pais;  // Obtener el país del token
  
      console.log('Login exitoso:', data);
      console.log('País del embajador:', pais);
      
      // Verificar si el entorno es localhost
      const isLocalhost = window.location.href.includes('localhost');
  
      // Si no es localhost, verificar la URL correcta según el país
      if (!isLocalhost) {
        const currentUrl = window.location.href;
        const isMXUrl = currentUrl.includes('rizosfelicesmx.unicornio.tech');
        const isCOUrl = currentUrl.includes('rizosfelicesco.unicornio.tech');
  
        if (pais === 'México' && !isMXUrl) {
          // Mostrar mensaje de redirección para México
          setShowRedirectMessage(true);
          setCorrectUrl('https://rizosfelicesmx.unicornio.tech');
          return;
        }
  
        if (pais === 'Colombia' && !isCOUrl) {
          // Mostrar mensaje de redirección para Colombia
          setShowRedirectMessage(true);
          setCorrectUrl('https://rizosfelicesco.unicornio.tech');
          return;
        }
      }
  
      // Guardar el token y el país en el localStorage
      localStorage.setItem('access_token', token);
      localStorage.setItem('pais', pais);
      const rol = decodedToken.rol;  // Obtener el rol del token
      localStorage.setItem('rol', rol);
      const nombre = decodedToken.nombre;  // Obtener el nombre del token
      localStorage.setItem('nombre', nombre);
  
      if (onLogin) {
        onLogin(token, pais);
      }
    } catch (error) {
      console.error('Error en la solicitud de login:', error);
      setErrorMessage('Error al conectar con el servidor');
    }
  };

  const handleRedirect = () => {
    window.location.href = correctUrl; // Redirigir a la URL correcta
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100">
      <Card className="w-full max-w-sm p-4 shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-center">Iniciar Sesión</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium leading-none text-gray-700">
                  Correo Electrónico
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="correo@ejemplo.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium leading-none text-gray-700">
                  Contraseña
                </label>
                <Input
                  id="password"
                  type="password"
                  placeholder="********"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>
            {errorMessage && <p className="text-red-500 text-sm">{errorMessage}</p>}
            {showRedirectMessage && (
              <div className="mt-4 p-4 bg-yellow-100 border border-yellow-400 text-yellow-700 rounded-md">
                <p className="text-sm font-medium">
                  Estás intentando iniciar sesión en la página incorrecta. Debes hacerlo en:{' '}
                  <a href={correctUrl} className="font-bold underline hover:text-yellow-800">
                    {correctUrl}
                  </a>
                </p>
                <div className="mt-3 flex flex-col space-y-2">
                  <Button
                    type="button"
                    className="w-full bg-yellow-500 hover:bg-yellow-600 text-white font-semibold py-2 rounded-md"
                    onClick={handleRedirect}
                  >
                    Ir a la página correcta
                  </Button>
                  <Button
                    type="button"
                    className="w-full bg-gray-500 hover:bg-gray-600 text-white font-semibold py-2 rounded-md"
                    onClick={() => setShowRedirectMessage(false)}
                  >
                    Cerrar
                  </Button>
                </div>
              </div>
            )}
            <CardFooter className="flex justify-center mt-6">
              <Button type="submit" className="w-full">
                Iniciar Sesión
              </Button>
            </CardFooter>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}