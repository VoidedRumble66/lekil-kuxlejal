'use client';

import React, { useMemo, useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { hierarchy, tree, HierarchyPointNode } from 'd3-hierarchy';
import { Home, ArrowLeft } from 'lucide-react';
import { PriorityDial } from './PriorityDial';

export interface PreziNodeData {
  id: string;
  title: string;
  subtitle?: string;
  priority_weight?: number;
  children?: PreziNodeData[];
  data?: Record<string, unknown>;
  isUnlocked?: boolean;
}

interface PreziViewerProps {
  data: PreziNodeData;
  onNodeClick?: (node: PreziNodeData) => void;
  onFocusChange?: (node: PreziNodeData) => void;
  onPriorityChange?: (node: PreziNodeData, newWeight: number) => void;
}

interface PointNode extends HierarchyPointNode<PreziNodeData> {
  cartesianX: number;
  cartesianY: number;
}

export function PreziViewer({ data, onNodeClick, onFocusChange, onPriorityChange }: PreziViewerProps) {
  // Configuración de la cámara
  const [camera, setCamera] = useState({ x: 0, y: 0, scale: 1 });
  const [activeNodeId, setActiveNodeId] = useState<string>(data.id);
  const [history, setHistory] = useState<string[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  const [isFocused, setIsFocused] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [lastPanPos, setLastPanPos] = useState({ x: 0, y: 0 });

  // Computar el layout del árbol de forma top-down
  const { nodes, links, nodeMap } = useMemo(() => {
    const root = hierarchy<PreziNodeData>(data);
    
    // Asignar un tamaño para cada nodo. Usaremos un layout top-down.
    // .nodeSize([width, height]).
    const layout = tree<PreziNodeData>()
      .nodeSize([250, 200]) // Separación entre nodos (X, Y)
      .separation((a, b) => (a.parent === b.parent ? 1 : 1.2));
      
    layout(root);

    const pointNodes = root.descendants() as PointNode[];
    const map = new Map<string, PointNode>();

    pointNodes.forEach((d) => {
      // D3 Tree asigna x (horizontal) y (profundidad vertical).
      d.cartesianX = d.x;
      d.cartesianY = d.y;
      map.set(d.data.id, d);
    });

    return {
      nodes: pointNodes,
      links: root.links() as unknown as { source: PointNode, target: PointNode }[],
      nodeMap: map
    };
  }, [data]);

  // Función para viajar a un nodo (Zoom + Pan)
  const focusOnNode = (id: string, pushToHistory = true) => {
    const node = nodeMap.get(id);
    if (!node) return;

    if (pushToHistory && activeNodeId !== id) {
      setHistory(prev => [...prev, activeNodeId]);
    }

    setActiveNodeId(id);
    
    // Calcular nivel de zoom basado en la profundidad
    // Más profundo = más zoom
    const zoomLevel = Math.max(1, 1 + (node.depth * 0.3));
    
    setCamera({
      x: -node.cartesianX * zoomLevel,
      y: -node.cartesianY * zoomLevel,
      scale: zoomLevel
    });

    if (onFocusChange) {
      onFocusChange(node.data);
    }
  };

  // Inicializar cámara en el nodo raíz al cargar
  useEffect(() => {
    focusOnNode(data.id, false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data.id]);

  // Click outside to remove focus
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsFocused(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Native wheel listener for zooming when focused (prevents page scroll)
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    
    const handleWheel = (e: WheelEvent) => {
      if (isFocused) {
        e.preventDefault();
        const zoomDelta = e.deltaY > 0 ? -0.1 : 0.1;
        setCamera(prev => ({
          ...prev,
          scale: Math.max(0.2, Math.min(4, prev.scale + zoomDelta))
        }));
      }
    };
    
    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, [isFocused]);

  const handleGoBack = () => {
    if (history.length === 0) return;
    const prevId = history[history.length - 1];
    setHistory(prev => prev.slice(0, -1));
    focusOnNode(prevId, false);
  };

  const handleGoHome = () => {
    setHistory([]);
    focusOnNode(data.id, false);
  };

  // Panning
  const handlePointerDown = (e: React.PointerEvent) => {
    if (e.button !== 0) return; // solo click izquierdo
    setIsFocused(true);
    setIsDragging(true);
    setLastPanPos({ x: e.clientX, y: e.clientY });
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - lastPanPos.x;
    const dy = e.clientY - lastPanPos.y;
    setLastPanPos({ x: e.clientX, y: e.clientY });
    
    setCamera(prev => ({
      ...prev,
      x: prev.x + (dx / prev.scale),
      y: prev.y + (dy / prev.scale)
    }));
  };

  const handlePointerUp = () => setIsDragging(false);

  return (
    <div 
      ref={containerRef}
      className={`relative w-full h-[600px] bg-slate-950 overflow-hidden rounded-2xl flex items-center justify-center shadow-inner transition-all duration-300 ${
        isFocused ? 'ring-2 ring-indigo-500 ring-offset-2' : ''
      } ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerLeave={handlePointerUp}
      style={{ backgroundImage: 'radial-gradient(circle at center, #1e293b 0%, #0f172a 100%)' }}
    >
      {/* Controles flotantes */}
      <div className="absolute top-4 left-4 z-20 flex space-x-2">
        <button 
          onClick={handleGoHome}
          className="p-2 bg-white/10 hover:bg-white/20 text-white rounded-full backdrop-blur-md transition-colors shadow-lg"
          title="Volver al inicio"
        >
          <Home size={20} />
        </button>
        {history.length > 0 && (
          <button 
            onClick={handleGoBack}
            className="p-2 bg-white/10 hover:bg-white/20 text-white rounded-full backdrop-blur-md transition-colors shadow-lg"
            title="Atrás"
          >
            <ArrowLeft size={20} />
          </button>
        )}
      </div>

      <div className="absolute top-4 right-4 z-20 text-xs text-white/50 bg-black/20 px-3 py-1.5 rounded-full backdrop-blur-sm">
        Zoom: {(camera.scale * 100).toFixed(0)}%
      </div>

      {/* El Lienzo 2D (Canvas) */}
      <motion.div
        className="absolute w-0 h-0" // Punto de anclaje centrado 0,0
        animate={{ 
          x: camera.x, 
          y: camera.y, 
          scale: camera.scale 
        }}
        transition={{ 
          type: "spring", 
          damping: 25, 
          stiffness: 90, 
          mass: 0.8 
        }}
        style={{ transformOrigin: "0 0" }} // Crítico para que la matemática coincida
      >
        {/* Dibujar Conexiones (Líneas) */}
        <svg className="absolute overflow-visible pointer-events-none" style={{ left: 0, top: 0 }}>
          {links.map((link, i) => {
            const { source: s, target: t } = link;
            // Curva en forma de S para un árbol vertical
            return (
              <motion.path
                key={`link-${i}`}
                d={`M${s.cartesianX},${s.cartesianY} C${s.cartesianX},${(s.cartesianY + t.cartesianY) / 2} ${t.cartesianX},${(s.cartesianY + t.cartesianY) / 2} ${t.cartesianX},${t.cartesianY}`}
                fill="none"
                stroke="rgba(255, 255, 255, 0.15)"
                strokeWidth={2}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 1.5, delay: t.depth * 0.2 }}
              />
            );
          })}
        </svg>

        {/* Dibujar Nodos */}
        {nodes.map((node) => {
          const isActive = activeNodeId === node.data.id;
          const isParentOfActive = history.includes(node.data.id);
          // Determinar si el nodo está cerca del activo para mostrarlo (ocultar ramas muy lejanas)
          // Para esta versión, mostramos todos pero jugamos con la opacidad.
          const depthDiff = Math.abs(node.depth - (nodeMap.get(activeNodeId)?.depth || 0));
          const opacity = depthDiff > 2 ? 0.2 : 1;

          return (
            <motion.div
              key={node.data.id}
              className="absolute flex flex-col items-center justify-center cursor-pointer group"
              style={{
                left: node.cartesianX,
                top: node.cartesianY,
                x: "-50%", // Centrar el div sobre su coordenada
                y: "-50%",
                zIndex: isActive ? 10 : 1
              }}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: opacity }}
              transition={{ 
                type: "spring", 
                delay: node.depth * 0.1,
                opacity: { duration: 0.5 }
              }}
              onClick={(e) => {
                e.stopPropagation();
                focusOnNode(node.data.id);
              }}
              onDoubleClick={(e) => {
                e.stopPropagation();
                if (onNodeClick) onNodeClick(node.data);
              }}
            >
              {node.data.priority_weight !== undefined && (
                <PriorityDial
                  value={node.data.priority_weight}
                  onChange={(val) => {
                    if (onPriorityChange) onPriorityChange(node.data, val);
                  }}
                  size={isActive ? 120 : isParentOfActive ? 88 : node.data.isUnlocked ? 80 : 72}
                  color={isActive ? '#818cf8' : '#f43f5e'}
                  disabled={node.data.id === 'root'}
                />
              )}
              {/* Círculo del nodo */}
              <div 
                className={`
                  relative flex items-center justify-center rounded-full shadow-2xl transition-all duration-300
                  ${isActive 
                    ? 'w-24 h-24 bg-indigo-500 border-4 border-white shadow-indigo-500/50' 
                    : isParentOfActive
                      ? 'w-16 h-16 bg-slate-700 border-2 border-slate-500'
                      : node.data.isUnlocked
                        ? 'w-14 h-14 bg-emerald-600 border-2 border-emerald-400 group-hover:border-emerald-300 group-hover:scale-110 shadow-[0_0_15px_rgba(52,211,153,0.5)]'
                        : 'w-12 h-12 bg-slate-800 border-2 border-slate-600 group-hover:border-indigo-400 group-hover:scale-110 opacity-70'
                  }
                `}
              >
                {/* Opcional: Icono o inicial */}
                <span className="text-white font-bold text-sm">
                  {node.data.title.substring(0, 2).toUpperCase()}
                </span>
                
                {/* Pulso para el activo */}
                {isActive && (
                  <span className="absolute inset-0 rounded-full animate-ping bg-white opacity-20"></span>
                )}
                {/* Pulso de desbloqueo sutil para los nodos desbloqueados que no están activos */}
                {!isActive && node.data.isUnlocked && !isParentOfActive && (
                  <span className="absolute inset-0 rounded-full animate-pulse bg-emerald-400 opacity-20"></span>
                )}
                
                {/* Etiqueta de Base Seleccionada */}
                {node.data.data?.hasBaseSelected === true && (
                  <div className="absolute -top-2 -right-2 bg-indigo-600 text-white text-[9px] font-bold px-1.5 py-0.5 rounded-full border-2 border-slate-900 shadow-md z-10">
                    ✓ BASE
                  </div>
                )}
              </div>
              
              {/* Título del nodo */}
              <div className={`
                absolute top-full mt-3 text-center whitespace-nowrap transition-all duration-300
                ${isActive ? 'scale-125' : 'group-hover:scale-110'}
              `}>
                <h3 className={`font-semibold drop-shadow-md ${isActive ? 'text-white' : 'text-slate-300'}`}>
                  {node.data.title}
                </h3>
                {node.data.subtitle && (
                  <p className="text-xs text-slate-400 drop-shadow-md">{node.data.subtitle}</p>
                )}
              </div>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
