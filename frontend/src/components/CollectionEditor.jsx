import React from 'react';
import { 
  DndContext, 
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { GripVertical, Eye, EyeOff, Trash2, Edit3 } from 'lucide-react';

const SortableItem = ({ id, item, type, onEdit, onDelete, onToggleVisibility }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div ref={setNodeRef} style={style} className="flex items-center gap-4 bg-white border border-warmBrown/5 p-4 mb-3 group">
      <div {...attributes} {...listeners} className="cursor-grab active:cursor-grabbing text-warmBrown/20 hover:text-accent transition-colors">
        <GripVertical size={16} />
      </div>

      <div className="flex-1 min-w-0">
        <h4 className="font-serif text-sm text-warmBrown truncate">
            {type === 'experience' ? item.company : 
             type === 'education' ? item.university :
             type === 'certifications' ? item.name :
             type === 'projects' ? item.name : 
             type === 'blog' ? item.title : 
             type === 'testimonials' ? item.name : 
             type === 'research' ? item.topic : (item.name || item.title || 'Untitled Artifact')}
        </h4>
        <p className="font-mono text-[9px] text-warmBrown/40 uppercase tracking-widest truncate">
            {type === 'experience' ? item.role : 
             type === 'education' ? item.degree :
             type === 'certifications' ? item.issuer :
             type === 'projects' ? item.techStack?.[0] || 'Portfolio Project' : 
             type === 'blog' ? item.category : 
             type === 'testimonials' ? item.role : 
             type === 'research' ? item.description : (item.level || item.id || 'Active Node')}
        </p>
      </div>

      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <button 
          onClick={() => onToggleVisibility(id)}
          className={`p-2 transition-colors ${item.visible !== false ? 'text-green-600 hover:bg-green-50' : 'text-warmBrown/20 hover:bg-ivory'}`}
        >
          {item.visible !== false ? <Eye size={14} /> : <EyeOff size={14} />}
        </button>
        <button onClick={() => onEdit(item)} className="p-2 text-warmBrown/40 hover:bg-ivory hover:text-accent transition-all">
          <Edit3 size={14} />
        </button>
        <button onClick={() => onDelete(id)} className="p-2 text-warmBrown/40 hover:bg-red-50 hover:text-red-500 transition-all">
          <Trash2 size={14} />
        </button>
      </div>
    </div>
  );
};

const CollectionEditor = ({ type, items, setItems, onEdit }) => {
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = (event) => {
    const { active, over } = event;
    if (active.id !== over.id) {
      const oldIndex = items.findIndex(i => (i.id || i.date || i.name) === active.id);
      const newIndex = items.findIndex(i => (i.id || i.date || i.name) === over.id);
      const newItems = arrayMove(items, oldIndex, newIndex).map((item, idx) => ({ ...item, order: idx }));
      setItems(newItems);
    }
  };

  const deleteItem = (id) => {
     if (window.confirm("Delete this artifact from history?")) {
        setItems(items.filter(i => (i.id || i.date || i.name) !== id));
     }
  };

  const toggleVisibility = (id) => {
    setItems(items.map(i => {
      if ((i.id || i.date || i.name) === id) {
        return { ...i, visible: i.visible === false ? true : false };
      }
      return i;
    }));
  };

  return (
    <div className="space-y-4">
      <DndContext 
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragEnd={handleDragEnd}
      >
        <SortableContext 
          items={items.map(i => (i.id || i.date || i.name))}
          strategy={verticalListSortingStrategy}
        >
          {items.map((item) => (
            <SortableItem 
              key={item.id || item.date || item.name} 
              id={item.id || item.date || item.name} 
              item={item} 
              type={type}
              onEdit={onEdit}
              onDelete={deleteItem}
              onToggleVisibility={toggleVisibility}
            />
          ))}
        </SortableContext>
      </DndContext>
      
      <button 
        onClick={() => onEdit({})}
        className="w-full py-4 border border-dashed border-warmBrown/10 text-warmBrown/30 font-mono text-[10px] uppercase tracking-[0.3em] hover:border-accent hover:text-accent transition-all"
      >
        + Annex New Entry
      </button>
    </div>
  );
};

export default CollectionEditor;
