"use client";

import { useState } from "react";
import type { AppUser } from "@/lib/types";

const COLORS = ["#4f46e5", "#0ea5e9", "#10b981", "#f59e0b", "#ec4899", "#8b5cf6"];

export default function ProfileSelector({
  users,
  onSelect,
  onCreate,
  busy,
}: {
  users: AppUser[];
  onSelect: (u: AppUser) => void;
  onCreate: (name: string) => void;
  busy: boolean;
}) {
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");

  return (
    <div className="ps-wrap">
      <h1 className="ps-title">¿Quién está usando PortfolioQuant?</h1>
      <p className="ps-sub">Elegí tu perfil o creá uno nuevo. Sin cuentas ni contraseñas.</p>

      <div className="ps-grid">
        {users.map((u, i) => (
          <button key={u.id} className="ps-card" onClick={() => onSelect(u)} disabled={busy}>
            <div className="ps-avatar" style={{ background: u.avatar_color || COLORS[i % COLORS.length] }}>
              {u.name.charAt(0).toUpperCase()}
            </div>
            <div className="ps-name">{u.name}</div>
          </button>
        ))}

        {!creating ? (
          <button className="ps-card" onClick={() => setCreating(true)} disabled={busy}>
            <div className="ps-avatar ps-add">+</div>
            <div className="ps-name">Nuevo perfil</div>
          </button>
        ) : (
          <div className="ps-card ps-form">
            <input
              autoFocus
              placeholder="Tu nombre"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter" && name.trim()) onCreate(name.trim()); }}
            />
            <div className="ps-formbtns">
              <button className="btn" disabled={!name.trim() || busy} onClick={() => onCreate(name.trim())}>
                {busy ? <span className="spinner" /> : "Crear"}
              </button>
              <button className="linkbtn" onClick={() => { setCreating(false); setName(""); }}>Cancelar</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
