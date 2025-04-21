¡Perfecto! Entonces te explico el **instructivo técnico paso a paso para hacer la conexión y transferencia entre máquinas con `scp`**, tal como lo hiciste en tu práctica.

---

## 🛠️ **Instructivo: Cómo empaquetar, comprimir y transferir archivos entre dos máquinas por terminal (con `scp`)**

---

### ✅ Requisitos previos:

1. 🐧 Dos equipos con Linux o Unix-like (puede ser máquina virtual o real)
2. ✅ SSH habilitado y corriendo en la máquina destino (`sshd`)
3. 👤 Un usuario válido y contraseña o acceso por llave SSH
4. 📡 Conectividad entre ambas máquinas (misma red o accesibles vía IP)

---

### 🔹 Paso 1: **Empaquetar y/o comprimir archivos**

#### Opción A – Solo empaquetar:
```bash
tar -cvf respaldo.tar carpeta/
```

#### Opción B – Empaquetar y comprimir con gzip:
```bash
tar -czvf respaldo.tar.gz carpeta/
```

---

### 🔹 Paso 2: **Verificar la IP de la máquina destino**

En la máquina remota (destino), ejecuta:

```bash
ip a
# o
hostname -I
```

Ejemplo de IP: `192.168.10.15`

---

### 🔹 Paso 3: **Transferir el archivo con `scp`**

Desde la máquina local (donde hiciste el `.tar.gz`), ejecutá:

```bash
scp respaldo.tar.gz usuario@192.168.10.15:/home/usuario/
```

🧠 Desglose:
- `respaldo.tar.gz` → archivo a enviar
- `usuario` → nombre de usuario remoto
- `192.168.10.15` → IP de la máquina destino
- `/home/usuario/` → ruta remota donde se guardará

Te pedirá la contraseña del usuario remoto (a menos que uses clave SSH).

---

### 🔹 Paso 4: **Extraer el archivo en la máquina destino**

Una vez copiado, en la máquina destino:

```bash
cd /home/usuario/
tar -xzvf respaldo.tar.gz
```

✅ ¡Listo! El contenido se descomprime con estructura completa.

---

### 🔒 Opcional – Transferencia con clave SSH (sin contraseña)

1. En la máquina local:
```bash
ssh-keygen -t ed25519
ssh-copy-id usuario@192.168.10.15
```

2. Luego `scp` funcionará sin pedir contraseña.

---

¿Querés que te arme un script que haga todo esto con logs y validaciones?
