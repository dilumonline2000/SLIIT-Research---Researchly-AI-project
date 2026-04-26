import { useState } from 'react';

interface SwitchProps {
  checked?: boolean;
  onCheckedChange?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export function Switch({ checked = false, onCheckedChange, disabled = false, className = '' }: SwitchProps) {
  const [isChecked, setIsChecked] = useState(checked);

  const handleChange = (newChecked: boolean) => {
    setIsChecked(newChecked);
    onCheckedChange?.(newChecked);
  };

  return (
    <button
      role="switch"
      aria-checked={isChecked}
      disabled={disabled}
      onClick={() => handleChange(!isChecked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
        isChecked ? 'bg-primary' : 'bg-gray-300'
      } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'} ${className}`}
    >
      <span
        className={`inline-block h-4 w-4 rounded-full bg-white transition-transform ${
          isChecked ? 'translate-x-6' : 'translate-x-1'
        }`}
      />
    </button>
  );
}
