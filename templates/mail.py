def generate_verification_email(codigo, tiempo_expiracion="15 minutos"):
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mail</title>
  <style>
    :root {{
      /* Colores principales basados en index.css */
      --color1: #fff; /* Blanco */
      --color2: #00a9d4; /* Azul claro */
      --color3: #1c3166; /* Azul oscuro */
      --color4: #240047; /* Púrpura oscuro */
      --color5: #1c0021; /* Casi negro */
      
      /* Variables adicionales */
      --color-acento: #00d4ff;
      --color-exito: #28a745;
      --color-advertencia: #ffc107;
      --color-peligro: #dc3545;
      --color-info: #17a2b8;
      --color-gris-claro: #f8f9fa;
      --color-gris-medio: #6c757d;
      --color-gris-oscuro: #343a40;
    }}

    body {{
      background: linear-gradient(135deg, var(--color1) 0%, rgba(0, 169, 212, 0.05) 100%);
      font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      margin: 0;
      padding: 20px;
      line-height: 1.6;
      color: var(--color5);
    }}

    .email-container {{
      max-width: 600px;
      margin: 0 auto;
      background: var(--color1);
      border-radius: 20px;
      overflow: hidden;
      box-shadow: 0 20px 40px rgba(0, 169, 212, 0.15);
      border: 1px solid rgba(0, 169, 212, 0.1);
      position: relative;
    }}

    .email-header {{
      background: linear-gradient(135deg, var(--color2) 0%, var(--color3) 50%, var(--color4) 100%);
      color: var(--color1);
      padding: 25px 25px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}

    .email-header-content {{
      position: relative;
      z-index: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 20px;
    }}

    .email-content {{
      padding: 50px 40px;
      background: var(--color1);
      position: relative;
    }}

    .email-greeting {{
      font-size: 2rem;
      margin-bottom: 25px;
      color: var(--color3);
      font-weight: 700;
      text-align: center;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 15px;
    }}

    .email-message {{
      font-size: 1.2rem;
      margin-bottom: 35px;
      line-height: 1.8;
      text-align: center;
      color: var(--color-gris-oscuro);
      font-weight: 400;
    }}

    .codigo-container {{
      background: linear-gradient(135deg, var(--color2) 0%, var(--color3) 50%, var(--color4) 100%);
      color: var(--color1);
      padding: 40px;
      border-radius: 25px;
      margin: 40px 0;
      text-align: center;
      box-shadow: 0 15px 35px rgba(0, 169, 212, 0.3);
      position: relative;
      overflow: hidden;
    }}

    .codigo-container::before {{
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
      animation: shine 4s infinite;
    }}

    @keyframes shine {{
      0% {{ left: -100%; }}
      100% {{ left: 100%; }}
    }}

    .codigo-container::after {{
      content: '';
      position: absolute;
      top: 10px;
      right: 10px;
      width: 60px;
      height: 60px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 50%;
      animation: pulse 2s infinite;
    }}

    @keyframes pulse {{
      0%, 100% {{ transform: scale(1); opacity: 0.3; }}
      50% {{ transform: scale(1.2); opacity: 0.1; }}
    }}

    .codigo-titulo {{
      margin: 0 0 20px 0;
      font-size: 1.5rem;
      font-weight: 600;
      opacity: 0.95;
      position: relative;
      z-index: 1;
    }}

    .codigo-numero {{
      font-size: 4rem;
      font-weight: 900;
      margin: 0;
      letter-spacing: 12px;
      text-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
      position: relative;
      z-index: 1;
      font-family: 'Inter', 'Courier New', monospace;
      background: rgba(255, 255, 255, 0.1);
      padding: 20px;
      border-radius: 15px;
      border: 2px solid rgba(255, 255, 255, 0.2);
    }}

    .codigo-subtitulo {{
      margin: 20px 0 0 0;
      font-size: 1.1rem;
      opacity: 0.9;
      position: relative;
      z-index: 1;
      font-weight: 500;
    }}

    .info-section {{
      display: grid;
      gap: 25px;
      margin: 35px 0;
    }}

    .email-info-box {{
      background: linear-gradient(135deg, rgba(0, 169, 212, 0.05), rgba(28, 49, 102, 0.05));
      border-left: 5px solid var(--color2);
      padding: 25px;
      border-radius: 15px;
      transition: all 0.3s ease;
    }}

    .email-info-box:hover {{
      transform: translateY(-2px);
      box-shadow: 0 8px 25px rgba(0, 169, 212, 0.1);
    }}

    .email-info-box h3 {{
      font-size: 1.4rem;
      color: var(--color3);
      margin: 0 0 15px 0;
      font-weight: 700;
      display: flex;
      align-items: center;
    }}

    .email-info-box p {{
      margin: 0;
      color: var(--color-gris-oscuro);
      font-size: 1.1rem;
      line-height: 1.7;
    }}

    .email-warning {{
      background: linear-gradient(135deg, rgba(255, 193, 7, 0.1), rgba(253, 126, 20, 0.1));
      border: 2px solid var(--color-advertencia);
      padding: 15px 10px;
      border-radius: 20px;
      text-align: center;
      position: relative;
      overflow: hidden;
    }}

    .email-warning h3 {{
      margin: 0 0 15px 0;
      font-size: 1.3rem;
      color: var(--color-advertencia);
      font-weight: 700;
    }}

    .email-warning p {{
      margin: 0;
      color: var(--color-gris-oscuro);
      font-size: 1rem;
      line-height: 1.6;
    }}

    .email-footer {{
      background: linear-gradient(135deg, var(--color-gris-claro), #e9ecef);
      text-align: center;
      padding: 35px 25px;
      color: var(--color-gris-medio);
      border-top: 1px solid rgba(0, 169, 212, 0.1);
      position: relative;
    }}

    .email-footer::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 50%;
      transform: translateX(-50%);
      width: 60px;
      height: 3px;
      background: linear-gradient(90deg, var(--color2), var(--color3));
      border-radius: 0 0 3px 3px;
    }}

    .footer-brand {{
      font-size: 1.5rem;
      font-weight: 900;
      color: var(--color3);
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 10px;
    }}

    .email-footer-links {{
      margin: 20px 0;
    }}

    .email-footer-links a {{
      color: var(--color2);
      text-decoration: none;
      margin: 0 20px;
      font-weight: 600;
      font-size: 1rem;
      transition: all 0.3s ease;
      position: relative;
    }}

    .email-footer-links a::after {{
      content: '';
      position: absolute;
      width: 100%;
      height: 2px;
      bottom: -3px;
      left: 0;
      background: var(--color2);
      transform: scaleX(0);
      transition: transform 0.3s ease;
    }}

    .email-footer-links a:hover {{
      color: var(--color3);
    }}

    .email-footer-links a:hover::after {{
      transform: scaleX(1);
    }}

    .footer-text {{
      font-size: 0.9rem;
      line-height: 1.6;
      margin-top: 20px;
    }}

    .footer-text strong {{
      color: var(--color3);
      font-weight: 700;
    }}

    /* Responsive Design */
    @media (max-width: 600px) {{
      body {{
        padding: 10px;
      }}
      
      .email-container {{
        border-radius: 15px;
      }}
      
      .email-header {{
        padding: 30px 20px;
      }}
      
      .email-content {{
        padding: 35px 25px;
      }}
      
      .codigo-numero {{
        font-size: 3rem;
        letter-spacing: 8px;
        padding: 15px;
      }}

      .email-greeting {{
        font-size: 1.6rem;
        flex-direction: column;
        gap: 10px;
      }}

      .email-message {{
        font-size: 1.1rem;
      }}

      .email-footer {{
        padding: 25px 20px;
      }}

      .email-footer-links a {{
        margin: 0 10px;
        font-size: 0.9rem;
      }}
    }}

    @media (max-width: 400px) {{
      .codigo-numero {{
        font-size: 2.5rem;
        letter-spacing: 4px;
      }}
      
      .email-greeting {{
        font-size: 1.4rem;
      }}
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <!-- Header -->
    <div class="email-header">
      <div class="email-header-content">
          <img src="/static/img/shared/logoheader.png" style="width: 200px;">
      </div>
    </div>

    <!-- Content -->
    <div class="email-content">
      <div class="email-greeting">
        Código de Verificación
      </div>

      <div class="email-message">
        Hemos recibido una solicitud para restablecer tu contraseña en <strong>!FC</strong>. 
        Utiliza el siguiente código de verificación para continuar con el proceso de forma segura.
      </div>

      <!-- Código de Verificación -->
      <div class="codigo-container">
        <h3 class="codigo-titulo">Tu código es:</h3>
        <div class="codigo-numero">{codigo}</div>
        <p class="codigo-subtitulo">Este código expira en {tiempo_expiracion}</p>
      </div>

      <!-- Info Sections -->
      <div class="info-section">
        <!-- Info Box -->
        <div class="email-info-box">
          <h3>
            Instrucciones
          </h3>
          <p>
            Ingresa este código en la página de recuperación de contraseña de <strong>!FC</strong> para continuar. 
            Si no solicitaste este cambio, puedes ignorar este correo de forma segura.
          </p>
        </div>

        <!-- Warning Box -->
        <div class="email-warning">
          <h3>Importante</h3>
          <p>Por tu seguridad, nunca compartas este código con nadie. El equipo de <strong>!FC</strong> nunca te pedirá este código por teléfono o email.</p>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="email-footer">
      <div class="footer-brand">
        <img src="/static/img/shared/logoabiertosinfondo.png" style="width: 70px;">
      </div>
      
      <div class="email-footer-links">
        <a href="#">Contacto</a>
      </div>
      
      <div class="footer-text">
        <strong>© 2025 !FC - Todos los derechos reservados</strong><br>
        <small>Este correo fue enviado desde nuestro sistema de seguridad automatizado</small><br>
      </div>
    </div>
  </div>
</body>
</html>
"""