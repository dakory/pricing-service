/* @ds-bundle: {"format":4,"namespace":"NicerHomesDesignSystem_ea7f10","components":[{"name":"Badge","sourcePath":"components/core/Badge.jsx"},{"name":"Button","sourcePath":"components/core/Button.jsx"},{"name":"Card","sourcePath":"components/core/Card.jsx"},{"name":"IconButton","sourcePath":"components/core/IconButton.jsx"},{"name":"Tag","sourcePath":"components/core/Tag.jsx"},{"name":"Dialog","sourcePath":"components/feedback/Dialog.jsx"},{"name":"Toast","sourcePath":"components/feedback/Toast.jsx"},{"name":"Tooltip","sourcePath":"components/feedback/Tooltip.jsx"},{"name":"Checkbox","sourcePath":"components/forms/Checkbox.jsx"},{"name":"Input","sourcePath":"components/forms/Input.jsx"},{"name":"InputWithSelectField","sourcePath":"components/forms/InputWithSelectField.jsx"},{"name":"LinkedValue","sourcePath":"components/forms/LinkedValue.jsx"},{"name":"Radio","sourcePath":"components/forms/Radio.jsx"},{"name":"Select","sourcePath":"components/forms/Select.jsx"},{"name":"Switch","sourcePath":"components/forms/Switch.jsx"},{"name":"Tabs","sourcePath":"components/navigation/Tabs.jsx"}],"sourceHashes":{"components/core/Badge.jsx":"29b00ec73a59","components/core/Button.jsx":"78bd377f17d0","components/core/Card.jsx":"7d09b3da7019","components/core/IconButton.jsx":"6a6f2e2cd8db","components/core/Tag.jsx":"e4240374056d","components/feedback/Dialog.jsx":"c351d47f6a13","components/feedback/Toast.jsx":"704809d48571","components/feedback/Tooltip.jsx":"7a0daaffa997","components/forms/Checkbox.jsx":"bbe6015804f0","components/forms/Input.jsx":"12ac5210c2a6","components/forms/InputWithSelectField.jsx":"c4b14c277798","components/forms/LinkedValue.jsx":"640d6d30af97","components/forms/Radio.jsx":"19dc60b7d7ce","components/forms/Select.jsx":"d0b0ffb37242","components/forms/Switch.jsx":"6e5906e0bcf3","components/navigation/Tabs.jsx":"8f964d4f0472","ui_kits/host-dashboard/Activity.jsx":"98c4d9d039d7","ui_kits/host-dashboard/App.jsx":"1d50775bb13a","ui_kits/host-dashboard/Pricing.jsx":"3f3b6687248f","ui_kits/marketing-site/PropertyDetail.jsx":"466bb7e64b2e"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.NicerHomesDesignSystem_ea7f10 = window.NicerHomesDesignSystem_ea7f10 || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// components/core/Badge.jsx
try { (() => {
function Badge({
  tone = 'neutral',
  children
}) {
  const tones = {
    neutral: {
      background: 'var(--surface-sunken)',
      color: 'var(--text-secondary)'
    },
    accent: {
      background: 'var(--action-accent-soft)',
      color: 'var(--color-ink-900)'
    },
    success: {
      background: 'var(--status-success-soft)',
      color: 'var(--status-success)'
    },
    danger: {
      background: 'var(--status-danger-soft)',
      color: 'var(--status-danger)'
    },
    inverse: {
      background: 'var(--color-ink-900)',
      color: 'var(--text-inverse)'
    }
  };
  return React.createElement('span', {
    style: {
      ...tones[tone],
      fontFamily: 'var(--font-sans)',
      fontSize: '12px',
      fontWeight: 600,
      padding: '3px 10px',
      borderRadius: 'var(--radius-full)',
      display: 'inline-flex',
      alignItems: 'center'
    }
  }, children);
}
Object.assign(__ds_scope, { Badge });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Badge.jsx", error: String((e && e.message) || e) }); }

// components/core/Button.jsx
try { (() => {
const sizeMap = {
  sm: {
    padding: '0 16px',
    fontSize: '13px',
    height: '38px'
  },
  md: {
    padding: '0 20px',
    fontSize: '14px',
    height: '44px'
  },
  lg: {
    padding: '0 26px',
    fontSize: '15px',
    height: '52px'
  }
};
function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  children,
  onClick,
  type = 'button',
  style: styleProp
}) {
  const base = {
    fontFamily: 'var(--font-sans)',
    fontWeight: 600,
    borderRadius: 'var(--radius-full)',
    border: '1px solid transparent',
    boxSizing: 'border-box',
    cursor: disabled ? 'default' : 'pointer',
    transition: 'background var(--duration-fast) var(--ease-standard), color var(--duration-fast) var(--ease-standard), border-color var(--duration-fast) var(--ease-standard)',
    opacity: disabled ? 0.45 : 1,
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    ...sizeMap[size]
  };
  const variants = {
    primary: {
      background: 'var(--action-primary)',
      color: 'var(--text-inverse)'
    },
    accent: {
      background: 'var(--action-accent)',
      color: 'var(--action-accent-ink)',
      boxShadow: 'var(--glow-accent)'
    },
    secondary: {
      background: 'var(--action-secondary)',
      color: 'var(--text-primary)',
      borderColor: 'var(--border-strong)'
    },
    ghost: {
      background: 'transparent',
      color: 'var(--text-primary)'
    }
  };
  const [hover, setHover] = React.useState(false);
  const hoverBg = {
    primary: 'var(--action-primary-hover)',
    accent: 'var(--action-accent-hover)',
    secondary: 'var(--action-secondary-hover)',
    ghost: 'var(--surface-sunken)'
  };
  const style = {
    ...base,
    ...variants[variant],
    ...styleProp
  };
  if (hover && !disabled) style.background = hoverBg[variant];
  return React.createElement('button', {
    type,
    disabled,
    style,
    onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, children);
}
Object.assign(__ds_scope, { Button });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Button.jsx", error: String((e && e.message) || e) }); }

// components/core/Card.jsx
try { (() => {
function Card({
  children,
  padding = 'var(--space-5)',
  elevated = false,
  glass = true,
  style
}) {
  return React.createElement('div', {
    style: {
      background: glass ? 'var(--surface-card)' : 'var(--surface-card-solid)',
      backdropFilter: glass ? 'blur(var(--glass-blur))' : 'none',
      WebkitBackdropFilter: glass ? 'blur(var(--glass-blur))' : 'none',
      border: glass ? '1px solid var(--glass-border)' : 'none',
      borderRadius: 'var(--radius-lg)',
      boxShadow: elevated ? 'var(--shadow-lg)' : 'var(--shadow-md)',
      padding,
      ...style
    }
  }, children);
}
Object.assign(__ds_scope, { Card });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Card.jsx", error: String((e && e.message) || e) }); }

// components/core/IconButton.jsx
try { (() => {
function IconButton({
  icon,
  label,
  size = 36,
  active = false,
  onClick
}) {
  const [hover, setHover] = React.useState(false);
  const style = {
    width: size,
    height: size,
    borderRadius: 'var(--radius-full)',
    border: 'none',
    background: active ? 'var(--surface-sunken)' : hover ? 'var(--surface-sunken)' : 'transparent',
    color: 'var(--text-primary)',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    transition: 'background var(--duration-fast) var(--ease-standard)'
  };
  return React.createElement('button', {
    type: 'button',
    'aria-label': label,
    title: label,
    style,
    onClick,
    onMouseEnter: () => setHover(true),
    onMouseLeave: () => setHover(false)
  }, icon);
}
Object.assign(__ds_scope, { IconButton });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/IconButton.jsx", error: String((e && e.message) || e) }); }

// components/core/Tag.jsx
try { (() => {
function Tag({
  children,
  onRemove
}) {
  return React.createElement('span', {
    style: {
      fontFamily: 'var(--font-sans)',
      fontSize: '12px',
      color: 'var(--text-primary)',
      border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-full)',
      padding: '4px 8px 4px 12px',
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px'
    }
  }, children, onRemove && React.createElement('button', {
    type: 'button',
    onClick: onRemove,
    style: {
      border: 'none',
      background: 'none',
      cursor: 'pointer',
      color: 'var(--text-muted)',
      fontSize: '14px',
      lineHeight: 1,
      padding: 0
    }
  }, '\u00d7'));
}
Object.assign(__ds_scope, { Tag });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/core/Tag.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Dialog.jsx
try { (() => {
function Dialog({
  open,
  title,
  children,
  onClose,
  footer
}) {
  if (!open) return null;
  return React.createElement('div', {
    style: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(11,12,14,0.4)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100
    }
  }, React.createElement('div', {
    style: {
      background: 'var(--surface-card-solid)',
      border: '1px solid var(--glass-border)',
      backdropFilter: 'blur(var(--glass-blur))',
      WebkitBackdropFilter: 'blur(var(--glass-blur))',
      borderRadius: 'var(--radius-lg)',
      boxShadow: 'var(--shadow-lg)',
      padding: 'var(--space-6)',
      width: 380,
      maxWidth: '90vw'
    }
  }, React.createElement('div', {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: 16
    }
  }, React.createElement('h3', {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: 20,
      margin: 0,
      color: 'var(--text-primary)'
    }
  }, title), React.createElement('button', {
    onClick: onClose,
    style: {
      border: 'none',
      background: 'none',
      cursor: 'pointer',
      fontSize: 18,
      color: 'var(--text-muted)'
    }
  }, '\u00d7')), React.createElement('div', {
    style: {
      color: 'var(--text-secondary)',
      fontSize: 14,
      lineHeight: 'var(--leading-relaxed)'
    }
  }, children), footer && React.createElement('div', {
    style: {
      marginTop: 24,
      display: 'flex',
      gap: 10,
      justifyContent: 'flex-end'
    }
  }, footer)));
}
Object.assign(__ds_scope, { Dialog });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Dialog.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Toast.jsx
try { (() => {
function Toast({
  tone = 'neutral',
  children,
  onClose
}) {
  const tones = {
    neutral: 'var(--color-ink-600)',
    success: 'var(--color-success-700)',
    danger: 'var(--color-danger)'
  };
  return React.createElement('div', {
    style: {
      background: tones[tone],
      color: '#fff',
      borderRadius: 'var(--radius-md)',
      padding: '12px 16px',
      display: 'flex',
      alignItems: 'center',
      gap: 12,
      fontFamily: 'var(--font-sans)',
      fontSize: 13,
      boxShadow: 'var(--shadow-md)',
      maxWidth: 340
    }
  }, React.createElement('span', {
    style: {
      flex: 1
    }
  }, children), onClose && React.createElement('button', {
    onClick: onClose,
    style: {
      border: 'none',
      background: 'none',
      color: 'rgba(255,255,255,0.7)',
      cursor: 'pointer',
      fontSize: 14
    }
  }, '\u00d7'));
}
Object.assign(__ds_scope, { Toast });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Toast.jsx", error: String((e && e.message) || e) }); }

// components/feedback/Tooltip.jsx
try { (() => {
function Tooltip({
  label,
  children
}) {
  const [show, setShow] = React.useState(false);
  return React.createElement('span', {
    style: {
      position: 'relative',
      display: 'inline-flex'
    },
    onMouseEnter: () => setShow(true),
    onMouseLeave: () => setShow(false)
  }, children, show && React.createElement('span', {
    style: {
      position: 'absolute',
      bottom: 'calc(100% + 8px)',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'var(--color-ink-600)',
      color: '#fff',
      fontSize: 12,
      padding: '5px 9px',
      borderRadius: 'var(--radius-sm)',
      whiteSpace: 'nowrap',
      fontFamily: 'var(--font-sans)',
      zIndex: 50,
      boxShadow: 'var(--shadow-md)'
    }
  }, label));
}
Object.assign(__ds_scope, { Tooltip });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/feedback/Tooltip.jsx", error: String((e && e.message) || e) }); }

// components/forms/Checkbox.jsx
try { (() => {
function Checkbox({
  label,
  checked,
  onChange
}) {
  return React.createElement('label', {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      fontFamily: 'var(--font-sans)',
      fontSize: 14,
      color: 'var(--text-primary)',
      cursor: 'pointer'
    }
  }, React.createElement('span', {
    onClick: () => onChange && onChange(!checked),
    style: {
      width: 18,
      height: 18,
      borderRadius: 'var(--radius-sm)',
      border: '1px solid ' + (checked ? 'var(--action-accent)' : 'var(--border-strong)'),
      background: checked ? 'var(--action-accent)' : 'var(--surface-card)',
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      transition: 'background var(--duration-fast) var(--ease-standard)'
    }
  }, checked && React.createElement('span', {
    style: {
      color: '#fff',
      fontSize: 11
    }
  }, '\u2713')), label);
}
Object.assign(__ds_scope, { Checkbox });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Checkbox.jsx", error: String((e && e.message) || e) }); }

// components/forms/Input.jsx
try { (() => {
function Input({
  label,
  type = 'text',
  placeholder,
  value,
  onChange,
  error,
  prefix
}) {
  const [focus, setFocus] = React.useState(false);
  return React.createElement('label', {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      fontFamily: 'var(--font-sans)'
    }
  }, label && React.createElement('span', {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: 'var(--text-secondary)'
    }
  }, label), React.createElement('div', {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      height: 38,
      boxSizing: 'border-box',
      border: '1px solid ' + (error ? 'var(--status-danger)' : focus ? 'var(--focus-ring)' : 'var(--border-default)'),
      borderRadius: 'var(--radius-full)',
      padding: '0 20px',
      background: 'var(--surface-card)',
      transition: 'border-color var(--duration-fast) var(--ease-standard)'
    }
  }, prefix && React.createElement('span', {
    style: {
      color: 'var(--text-muted)',
      fontSize: 14
    }
  }, prefix), React.createElement('input', {
    type,
    placeholder,
    value,
    onChange,
    onFocus: () => setFocus(true),
    onBlur: () => setFocus(false),
    style: {
      border: 'none',
      outline: 'none',
      fontSize: 14,
      fontFamily: 'var(--font-sans)',
      color: 'var(--text-primary)',
      width: '100%',
      background: 'transparent'
    }
  })), error && React.createElement('span', {
    style: {
      fontSize: 12,
      color: 'var(--status-danger)'
    }
  }, error));
}
Object.assign(__ds_scope, { Input });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Input.jsx", error: String((e && e.message) || e) }); }

// components/forms/LinkedValue.jsx
try { (() => {
function LinkedValue({
  children
}) {
  return React.createElement('span', {
    style: {
      fontSize: 12.5,
      fontWeight: 600,
      color: 'var(--text-secondary)',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis',
      background: 'var(--color-line)',
      borderRadius: 'var(--radius-full)',
      padding: '4px 10px',
      display: 'inline-block'
    }
  }, children);
}
Object.assign(__ds_scope, { LinkedValue });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/LinkedValue.jsx", error: String((e && e.message) || e) }); }

// components/forms/InputWithSelectField.jsx
try { (() => {
function InputWithSelectField({
  label,
  options = [],
  value,
  onChange,
  placeholder = 'Enter a value'
}) {
  const [focused, setFocused] = React.useState(false);
  const [activeIdx, setActiveIdx] = React.useState(-1);
  const ref = React.useRef(null);
  const isMatchedOption = options.some(o => o.value === value);
  const isCustom = value != null && value !== '' && !isMatchedOption;
  const selectedOpt = options.find(o => o.value === value);
  React.useEffect(() => {
    if (!focused) return;
    const onDoc = e => {
      if (ref.current && !ref.current.contains(e.target)) setFocused(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [focused]);
  React.useEffect(() => {
    if (focused) setActiveIdx(-1);
  }, [focused]);
  const displayLabel = opt => opt.linked ? React.createElement(__ds_scope.LinkedValue, {
    key: opt.value
  }, opt.label) : React.createElement('span', {
    style: {
      fontSize: 14,
      fontWeight: 400,
      color: 'var(--text-secondary)',
      whiteSpace: 'nowrap',
      overflow: 'hidden',
      textOverflow: 'ellipsis'
    }
  }, opt.label);
  const selectOption = opt => {
    onChange && onChange(opt.value);
    setFocused(false);
  };
  const onKeyDown = e => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIdx(i => Math.min(i + 1, options.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIdx(i => Math.max(i - 1, -1));
    } else if (e.key === 'Enter' && activeIdx >= 0) {
      e.preventDefault();
      selectOption(options[activeIdx]);
    } else if (e.key === 'Escape') {
      setFocused(false);
    }
  };
  const rowStyle = (selected, active) => ({
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: 38,
    padding: '0 20px',
    flexShrink: 0,
    background: selected ? '#F5F5F5' : active ? 'var(--color-mist)' : 'transparent',
    cursor: 'pointer'
  });
  return React.createElement('label', {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      fontFamily: 'var(--font-sans)'
    }
  }, label ? React.createElement('span', {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: 'var(--text-secondary)'
    }
  }, label) : null, React.createElement('div', {
    ref: ref,
    style: {
      position: 'relative',
      height: 38
    }
  }, React.createElement('div', {
    style: {
      position: focused ? 'absolute' : 'static',
      top: 0,
      left: 0,
      right: 0,
      border: '1px solid ' + (focused ? 'var(--focus-ring)' : 'var(--border-default)'),
      borderRadius: 19,
      overflow: 'hidden',
      transition: 'border-color var(--duration-fast) var(--ease-standard)',
      background: 'var(--color-white)',
      boxShadow: focused ? 'var(--shadow-lg)' : 'none',
      zIndex: 10
    }
  }, !focused ? React.createElement('div', {
    onClick: () => setFocused(true),
    style: {
      height: 38,
      display: 'flex',
      alignItems: 'center',
      padding: '0 20px',
      cursor: 'text'
    }
  }, isCustom ? React.createElement('span', {
    style: {
      fontSize: 14,
      color: 'var(--text-primary)'
    }
  }, value) : selectedOpt ? displayLabel(selectedOpt) : React.createElement('span', {
    style: {
      fontSize: 14,
      color: 'var(--text-muted)'
    }
  }, placeholder)) : React.createElement('div', {
    style: rowStyle(isCustom, activeIdx === -1),
    onMouseEnter: () => setActiveIdx(-1)
  }, React.createElement('input', {
    autoFocus: true,
    value: isCustom ? value : '',
    onChange: e => onChange && onChange(e.target.value),
    onFocus: () => setFocused(true),
    onKeyDown,
    placeholder,
    style: {
      border: 'none',
      outline: 'none',
      background: 'transparent',
      fontSize: 14,
      fontWeight: 400,
      fontFamily: 'var(--font-sans)',
      color: 'var(--text-primary)',
      width: '100%',
      padding: 0,
      margin: 0
    }
  }), isCustom ? React.createElement('img', {
    src: 'https://unpkg.com/lucide-static@latest/icons/check.svg',
    style: {
      width: 14,
      height: 14,
      opacity: 0.5,
      flexShrink: 0
    }
  }) : null), focused && options.length > 0 ? React.createElement('div', {
    style: {
      maxHeight: 38 * 4,
      overflowY: 'auto'
    }
  }, options.map((opt, i) => {
    const selected = opt.value === value;
    return React.createElement('div', {
      key: opt.value,
      onMouseDown: e => {
        e.preventDefault();
        selectOption(opt);
      },
      onMouseEnter: () => setActiveIdx(i),
      style: rowStyle(selected, activeIdx === i)
    }, displayLabel(opt), selected ? React.createElement('img', {
      src: 'https://unpkg.com/lucide-static@latest/icons/check.svg',
      style: {
        width: 14,
        height: 14,
        opacity: 0.5,
        flexShrink: 0
      }
    }) : null);
  })) : null)));
}
Object.assign(__ds_scope, { InputWithSelectField });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/InputWithSelectField.jsx", error: String((e && e.message) || e) }); }

// components/forms/Radio.jsx
try { (() => {
function Radio({
  label,
  checked,
  onChange,
  name
}) {
  return React.createElement('label', {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 8,
      fontFamily: 'var(--font-sans)',
      fontSize: 14,
      color: 'var(--text-primary)',
      cursor: 'pointer'
    }
  }, React.createElement('span', {
    onClick: () => onChange && onChange(),
    style: {
      width: 18,
      height: 18,
      borderRadius: 'var(--radius-full)',
      border: '1px solid ' + (checked ? 'var(--action-accent)' : 'var(--border-strong)'),
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center'
    }
  }, checked && React.createElement('span', {
    style: {
      width: 9,
      height: 9,
      borderRadius: 'var(--radius-full)',
      background: 'var(--action-accent)'
    }
  })), label);
}
Object.assign(__ds_scope, { Radio });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Radio.jsx", error: String((e && e.message) || e) }); }

// components/forms/Select.jsx
try { (() => {
function Select({
  label,
  options = [],
  value,
  onChange,
  pill = true
}) {
  return React.createElement('label', {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6,
      fontFamily: 'var(--font-sans)'
    }
  }, label && React.createElement('span', {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: 'var(--text-secondary)'
    }
  }, label), React.createElement('select', {
    value,
    onChange,
    style: {
      border: '1px solid var(--border-default)',
      borderRadius: 'var(--radius-full)',
      height: 38,
      boxSizing: 'border-box',
      padding: '0 36px 0 20px',
      fontSize: 14,
      fontWeight: pill ? 600 : 400,
      fontFamily: 'var(--font-sans)',
      color: 'var(--text-primary)',
      background: 'var(--surface-card)',
      appearance: 'none',
      WebkitAppearance: 'none',
      backgroundImage: 'url("https://unpkg.com/lucide-static@latest/icons/chevron-down.svg")',
      backgroundRepeat: 'no-repeat',
      backgroundPosition: 'right 14px center',
      backgroundSize: '14px',
      cursor: 'pointer'
    }
  }, options.map(o => React.createElement('option', {
    key: o.value || o,
    value: o.value || o
  }, o.label || o))));
}
Object.assign(__ds_scope, { Select });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Select.jsx", error: String((e && e.message) || e) }); }

// components/forms/Switch.jsx
try { (() => {
function Switch({
  checked,
  onChange,
  label
}) {
  return React.createElement('label', {
    style: {
      display: 'inline-flex',
      alignItems: 'center',
      gap: 10,
      fontFamily: 'var(--font-sans)',
      fontSize: 14,
      color: 'var(--text-primary)',
      cursor: 'pointer'
    }
  }, React.createElement('span', {
    onClick: () => onChange && onChange(!checked),
    style: {
      width: 38,
      height: 22,
      borderRadius: 'var(--radius-full)',
      background: checked ? 'var(--action-accent)' : 'var(--border-strong)',
      position: 'relative',
      transition: 'background var(--duration-standard) var(--ease-standard)'
    }
  }, React.createElement('span', {
    style: {
      position: 'absolute',
      top: 2,
      left: checked ? 18 : 2,
      width: 18,
      height: 18,
      borderRadius: 'var(--radius-full)',
      background: '#fff',
      transition: 'left var(--duration-standard) var(--ease-standard)',
      boxShadow: 'var(--shadow-sm)'
    }
  })), label);
}
Object.assign(__ds_scope, { Switch });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/forms/Switch.jsx", error: String((e && e.message) || e) }); }

// components/navigation/Tabs.jsx
try { (() => {
function Tabs({
  items = [],
  value,
  onChange
}) {
  return React.createElement('div', {
    style: {
      display: 'flex',
      gap: 24,
      borderBottom: '1px solid var(--border-default)',
      fontFamily: 'var(--font-sans)'
    }
  }, items.map(it => {
    const active = it.value === value;
    return React.createElement('button', {
      key: it.value,
      onClick: () => onChange && onChange(it.value),
      style: {
        border: 'none',
        background: 'none',
        cursor: 'pointer',
        padding: '10px 0',
        fontSize: 14,
        fontWeight: 500,
        color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
        borderBottom: '2px solid ' + (active ? 'var(--action-accent)' : 'transparent'),
        marginBottom: -1
      }
    }, it.label);
  }));
}
Object.assign(__ds_scope, { Tabs });
})(); } catch (e) { __ds_ns.__errors.push({ path: "components/navigation/Tabs.jsx", error: String((e && e.message) || e) }); }

// ui_kits/host-dashboard/Activity.jsx
try { (() => {
const {
  Badge,
  Card
} = window.NicerHomesDesignSystem_ea7f10;
function relTime(mins) {
  if (mins < 60) return mins + 'm ago';
  const h = Math.floor(mins / 60);
  if (h < 24) return h + 'h ago';
  return Math.floor(h / 24) + 'd ago';
}
function Activity() {
  const events = [{
    type: 'Price update',
    scope: 'Villa Kayu \u00b7 Beachfront Collection',
    detail: 'Applied 6 recommended price changes for August\u2013September.',
    status: 'success',
    mins: 4
  }, {
    type: 'Competitor sync',
    scope: 'Uluwatu market',
    detail: 'Refreshed rates from 14 comparable listings.',
    status: 'success',
    mins: 22
  }, {
    type: 'Price fetch',
    scope: 'All properties',
    detail: 'Pulled current live rates from connected channels.',
    status: 'success',
    mins: 41
  }, {
    type: 'Market data collection',
    scope: 'Canggu market',
    detail: 'Collecting demand signals for the next 90 days.',
    status: 'running',
    mins: 2
  }, {
    type: 'Price update',
    scope: 'Rumah Terang \u00b7 Ubud Retreats',
    detail: '2 of 5 recommended changes applied \u2014 3 skipped (below minimum rate).',
    status: 'warning',
    mins: 96
  }, {
    type: 'Competitor sync',
    scope: 'Ubud market',
    detail: 'Could not reach one data source; retried automatically.',
    status: 'error',
    mins: 130
  }, {
    type: 'Price fetch',
    scope: 'Villa Alang',
    detail: 'Pulled current live rates from connected channels.',
    status: 'success',
    mins: 260
  }, {
    type: 'Market data collection',
    scope: 'All markets',
    detail: 'Weekly demand and event scan completed.',
    status: 'success',
    mins: 1400
  }];
  const tones = {
    success: 'success',
    warning: 'accent',
    error: 'danger',
    running: 'neutral'
  };
  const labels = {
    success: 'Completed',
    warning: 'Needs review',
    error: 'Failed',
    running: 'Running'
  };
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0,
      padding: '0 40px 40px',
      overflow: 'auto'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12,
      maxWidth: 760
    }
  }, events.map((e, i) => /*#__PURE__*/React.createElement(Card, {
    key: i,
    padding: "16px 20px",
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 16
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      width: 8,
      height: 8,
      borderRadius: 'var(--radius-full)',
      flexShrink: 0,
      background: e.status === 'running' ? 'var(--color-accent-500)' : e.status === 'error' ? 'var(--status-danger)' : e.status === 'warning' ? 'var(--color-accent-700)' : 'var(--status-success)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      marginBottom: 2
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      fontSize: 14,
      color: 'var(--text-primary)'
    }
  }, e.type), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      color: 'var(--text-secondary)'
    }
  }, e.scope)), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: 'var(--text-secondary)'
    }
  }, e.detail)), /*#__PURE__*/React.createElement(Badge, {
    tone: tones[e.status]
  }, labels[e.status]), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--text-muted)',
      width: 70,
      textAlign: 'right',
      flexShrink: 0
    }
  }, relTime(e.mins))))));
}
window.Activity = Activity;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/host-dashboard/Activity.jsx", error: String((e && e.message) || e) }); }

// ui_kits/host-dashboard/App.jsx
try { (() => {
const {
  IconButton
} = window.NicerHomesDesignSystem_ea7f10;
function Sidebar({
  section,
  onSection,
  collapsed,
  onToggleCollapsed
}) {
  const [peek, setPeek] = React.useState(false);
  const items = [{
    label: 'Calendar',
    value: 'pricing'
  }, {
    label: 'Activity',
    value: 'activity'
  }];
  const content = /*#__PURE__*/React.createElement("div", {
    onMouseLeave: () => setPeek(false),
    style: {
      width: 240,
      padding: '28px 0',
      display: 'flex',
      flexDirection: 'column',
      gap: 2,
      background: 'var(--color-mist)',
      overflow: 'hidden',
      flexShrink: 0,
      minHeight: '100vh',
      boxSizing: 'border-box'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 28,
      marginTop: -6,
      paddingLeft: 20,
      paddingRight: 16,
      minWidth: 220
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontFamily: 'var(--font-logo)',
      fontSize: 20,
      letterSpacing: '0.01em',
      color: 'var(--color-logo-text)'
    }
  }, "nicer"), /*#__PURE__*/React.createElement(IconButton, {
    label: "Collapse sidebar",
    onClick: onToggleCollapsed,
    icon: /*#__PURE__*/React.createElement("img", {
      src: "https://unpkg.com/lucide-static@latest/icons/chevrons-left.svg",
      style: {
        width: 15,
        height: 15
      }
    }),
    size: 28
  })), items.map(it => {
    const [hover, setHover] = React.useState(false);
    const active = section === it.value;
    return /*#__PURE__*/React.createElement("div", {
      key: it.value,
      onClick: () => onSection(it.value),
      onMouseEnter: () => setHover(true),
      onMouseLeave: () => setHover(false),
      style: {
        margin: '0 8px',
        padding: '10px 12px',
        borderRadius: 'var(--radius-md)',
        fontFamily: 'var(--font-sans)',
        fontSize: 14,
        fontWeight: 600,
        cursor: 'pointer',
        whiteSpace: 'nowrap',
        minWidth: 204,
        color: active ? 'var(--text-primary)' : 'var(--text-secondary)',
        background: active ? 'rgba(11,12,14,0.06)' : hover ? 'rgba(11,12,14,0.04)' : 'transparent'
      }
    }, it.label);
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1
    }
  }));
  if (collapsed) {
    return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      onMouseEnter: () => setPeek(true),
      style: {
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
        width: 14,
        zIndex: 39
      }
    }), !peek && /*#__PURE__*/React.createElement("div", {
      style: {
        position: 'fixed',
        left: 24,
        top: 20,
        zIndex: 41
      }
    }, /*#__PURE__*/React.createElement(IconButton, {
      label: "Open sidebar",
      onClick: onToggleCollapsed,
      icon: /*#__PURE__*/React.createElement("img", {
        src: "https://unpkg.com/lucide-static@latest/icons/chevrons-right.svg",
        style: {
          width: 15,
          height: 15
        }
      }),
      size: 32
    })), /*#__PURE__*/React.createElement("div", {
      style: {
        position: 'fixed',
        left: 0,
        top: 0,
        height: '100vh',
        zIndex: 40,
        transform: `translateX(${peek ? '0' : '-100%'})`,
        transition: 'transform var(--duration-standard) var(--ease-standard)',
        boxShadow: peek ? 'var(--shadow-lg)' : 'none'
      }
    }, content));
  }
  return content;
}
function TopBar({
  title
}) {
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '28px 40px 0',
      position: 'relative',
      zIndex: 1,
      background: 'var(--color-white)'
    }
  }, /*#__PURE__*/React.createElement("h2", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 500,
      fontSize: 'var(--text-xl)',
      margin: 0,
      color: 'var(--text-primary)'
    }
  }, title));
}
function HostDashboardApp() {
  const [section, setSection] = React.useState('pricing');
  const [collapsed, setCollapsed] = React.useState(false);
  const screens = {
    pricing: window.Pricing,
    activity: window.Activity
  };
  const titles = {
    pricing: 'Pricing & calendar',
    activity: 'Activity'
  };
  const Screen = screens[section];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      minHeight: '100vh',
      fontFamily: 'var(--font-sans)',
      background: 'var(--surface-page)',
      position: 'relative',
      overflow: 'hidden'
    }
  }, /*#__PURE__*/React.createElement(Sidebar, {
    section: section,
    onSection: setSection,
    collapsed: collapsed,
    onToggleCollapsed: () => setCollapsed(c => !c)
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      position: 'relative',
      zIndex: 1,
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
      minWidth: 0,
      paddingTop: 40,
      boxSizing: 'border-box'
    }
  }, section === 'activity' && /*#__PURE__*/React.createElement(TopBar, {
    title: titles[section]
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '24px 0 0 0',
      flex: 1,
      display: 'flex',
      minHeight: 0,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement(Screen, null))));
}
window.HostDashboardApp = HostDashboardApp;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/host-dashboard/App.jsx", error: String((e && e.message) || e) }); }

// ui_kits/host-dashboard/Pricing.jsx
try { (() => {
const {
  Input,
  IconButton,
  Select,
  Button,
  Toast,
  Switch,
  InputWithSelectField
} = window.NicerHomesDesignSystem_ea7f10;
function UrgencyRulesEditor({
  rules,
  setRules
}) {
  const [hover, setHover] = React.useState(null);
  const sorted = [...rules].sort((a, b) => a.f - b.f);
  const display = [];
  let cursor = 0;
  sorted.forEach(r => {
    if (r.f > cursor) display.push({
      f: cursor,
      t: r.f - 1,
      d: 0,
      gap: true
    });
    display.push(r);
    cursor = r.t + 1;
  });
  const max = Math.max(1, cursor);
  const maxAbsD = Math.max(...rules.map(r => Math.abs(parseFloat(r.d)) || 0), 0.0001);
  const colorFor = r => {
    const a = r.gap ? 0 : 0.22 + 0.78 * (Math.abs(parseFloat(r.d)) || 0) / maxAbsD;
    return `rgba(39,17,242,${a})`;
  };
  const pct = r => `${Math.round(parseFloat(r.d) * 100)}%`;
  const update = (i, k, v) => setRules(rs => rs.map((r, idx) => idx === i ? {
    ...r,
    [k]: v
  } : r));
  const remove = i => setRules(rs => rs.filter((_, idx) => idx !== i));
  const add = () => setRules(rs => {
    const last = rs[rs.length - 1];
    const f = last ? last.t + 1 : 0;
    return [...rs, {
      f,
      t: f + 3,
      d: -0.05
    }];
  });
  const addGap = g => setRules(rs => [...rs, {
    f: g.f,
    t: g.t,
    d: 0
  }]);
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'relative',
      height: 72,
      marginBottom: 8,
      display: 'flex',
      alignItems: 'flex-end',
      gap: 0
    }
  }, display.map((r, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    onMouseEnter: () => setHover(i),
    onMouseLeave: () => setHover(h => h === i ? null : h),
    style: {
      width: `${(r.t - r.f + 1) / max * 100}%`,
      height: `${r.gap ? 4 : Math.max(6, (Math.abs(parseFloat(r.d)) || 0) / maxAbsD * 100)}%`,
      background: colorFor(r),
      position: 'relative',
      marginRight: i < display.length - 1 ? 2 : 0,
      borderRadius: 4,
      cursor: 'default'
    }
  }, hover === i && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      bottom: 'calc(100% + 8px)',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'var(--color-ink-900)',
      color: 'var(--color-white)',
      fontSize: 11,
      fontWeight: 600,
      padding: '6px 10px',
      borderRadius: 'var(--radius-sm)',
      whiteSpace: 'nowrap',
      zIndex: 5,
      boxShadow: 'var(--shadow-md)'
    }
  }, "Day ", r.f, "\u2013", r.t, ": ", pct(r))))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: 10.5,
      color: 'var(--text-muted)',
      marginBottom: 22
    }
  }, /*#__PURE__*/React.createElement("span", null, "Day 0"), /*#__PURE__*/React.createElement("span", null, "Day ", max - 1)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 6
    }
  }, display.map((r, i) => r.gap ? /*#__PURE__*/React.createElement("div", {
    key: 'gap' + i,
    onClick: () => addGap(r),
    style: {
      borderRadius: 'var(--radius-md)',
      padding: '10px 14px',
      display: 'flex',
      alignItems: 'center',
      gap: 14,
      background: 'rgba(11,12,14,0.03)',
      cursor: 'pointer'
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: 'var(--text-muted)',
      minWidth: 90
    }
  }, "Day ", r.f, "\u2013", r.t), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11.5,
      color: 'var(--text-muted)',
      flex: 1
    }
  }, "Gap \u2014 click to set a discount")) : (() => {
    const idx = rules.indexOf(r);
    return /*#__PURE__*/React.createElement("div", {
      key: idx,
      style: {
        borderRadius: 'var(--radius-md)',
        padding: '8px 14px',
        display: 'flex',
        alignItems: 'center',
        gap: 16
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        fontWeight: 600,
        color: 'var(--text-primary)',
        minWidth: 80,
        flexShrink: 0
      }
    }, "Day ", /*#__PURE__*/React.createElement("input", {
      className: "tf2",
      style: {
        width: 26,
        textAlign: 'center',
        display: 'inline',
        borderRadius: 'var(--radius-sm)'
      },
      value: r.f,
      onChange: e => update(idx, 'f', +e.target.value || 0)
    }), "\u2013", /*#__PURE__*/React.createElement("input", {
      className: "tf2",
      style: {
        width: 26,
        textAlign: 'center',
        display: 'inline',
        borderRadius: 'var(--radius-sm)'
      },
      value: r.t,
      onChange: e => update(idx, 't', +e.target.value || 0)
    })), /*#__PURE__*/React.createElement("input", {
      type: "range",
      className: "rng2",
      min: "0",
      max: "50",
      value: Math.round(Math.abs(parseFloat(r.d)) * 100) || 0,
      onChange: e => update(idx, 'd', (-+e.target.value / 100).toFixed(2)),
      style: {
        flex: 1
      }
    }), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        fontWeight: 700,
        color: 'var(--text-primary)',
        width: 34,
        textAlign: 'right'
      }
    }, pct(r)), /*#__PURE__*/React.createElement(IconButton, {
      label: "Remove",
      onClick: () => remove(idx),
      icon: /*#__PURE__*/React.createElement("img", {
        src: "https://unpkg.com/lucide-static@latest/icons/x.svg",
        style: {
          width: 12,
          height: 12,
          opacity: 0.5
        }
      })
    }));
  })()), /*#__PURE__*/React.createElement("div", {
    onClick: add,
    style: {
      borderRadius: 'var(--radius-md)',
      padding: '10px 14px',
      display: 'flex',
      alignItems: 'center',
      gap: 8,
      opacity: 0.35,
      cursor: 'pointer'
    },
    onMouseEnter: e => e.currentTarget.style.opacity = 0.65,
    onMouseLeave: e => e.currentTarget.style.opacity = 0.35
  }, /*#__PURE__*/React.createElement("img", {
    src: "https://unpkg.com/lucide-static@latest/icons/plus.svg",
    style: {
      width: 13,
      height: 13
    }
  }), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 12,
      fontWeight: 600,
      color: 'var(--text-secondary)'
    }
  }, "Add period"))));
}
function genDays(n) {
  const start = new Date(2026, 7, 28);
  return Array.from({
    length: n
  }, (_, i) => {
    const d = new Date(start);
    d.setDate(start.getDate() + i);
    return d;
  });
}
function monthLabel(d) {
  return d.toLocaleDateString('en-US', {
    month: 'long',
    year: 'numeric'
  });
}
function Pricing() {
  const days = genDays(28);
  const listings = [{
    name: 'Villa Kayu',
    c: 'var(--color-accent-300)',
    base: 4850000,
    group: 'Beachfront Collection'
  }, {
    name: 'Villa Alang',
    c: 'var(--color-mist)',
    base: 3200000,
    group: 'Beachfront Collection'
  }, {
    name: 'Rumah Terang',
    c: 'var(--color-ink-200)',
    base: 5400000,
    group: 'Ubud Retreats'
  }];
  const groupOrder = [];
  listings.forEach(l => {
    if (!groupOrder.includes(l.group)) groupOrder.push(l.group);
  });
  let rowCursor = 3;
  let propCursor = 0;
  const groups = groupOrder.map(gname => {
    const items = listings.filter(l => l.group === gname);
    const row = rowCursor;
    rowCursor += 1;
    items.forEach(it => {
      it.row = rowCursor;
      rowCursor += 1;
      it.propIndex = propCursor;
      propCursor += 1;
    });
    return {
      name: gname,
      items,
      row
    };
  });
  const totalRows = rowCursor;
  const [selected, setSelected] = React.useState(null);
  const [hoverCellKey, setHoverCellKey] = React.useState(null);
  const [rangeAnchor, setRangeAnchor] = React.useState(null);
  const [rangeSelection, setRangeSelection] = React.useState(null);
  const lastPointer = React.useRef({
    x: 0,
    y: 0
  });
  const [toast, setToast] = React.useState(null);
  const [busy, setBusy] = React.useState(null);
  const [lastSync, setLastSync] = React.useState({
    fetch: '2 hours ago',
    comp: 'Yesterday at 6:40 PM',
    generate: '5 hours ago',
    apply: '3 days ago'
  });
  const [actionsOpen, setActionsOpen] = React.useState(false);
  const [globalOpen, setGlobalOpen] = React.useState(false);
  const [globalSettings, setGlobalSettings] = React.useState({
    minComp: '3',
    positioning: '1',
    guestToHost: '0.839',
    minIDR: '900,000',
    maxIDR: '1,800,000',
    step: '1,000',
    useUrgency: 'on',
    method: 'median',
    manualBase: '',
    rules: [{
      f: 0,
      t: 3,
      d: -0.3
    }, {
      f: 4,
      t: 7,
      d: -0.2
    }, {
      f: 8,
      t: 14,
      d: -0.1
    }, {
      f: 15,
      t: 30,
      d: -0.05
    }]
  });
  const setGlobalField = (field, val) => setGlobalSettings(s => ({
    ...s,
    [field]: val
  }));
  const saveGlobal = () => {
    setToast('Global settings saved.');
    setTimeout(() => setToast(null), 2600);
    setGlobalOpen(false);
  };
  const [tooltipData, setTooltipData] = React.useState(null);
  const [priceOverrides, setPriceOverrides] = React.useState({});
  const [rangePriceInput, setRangePriceInput] = React.useState('');
  const [propertyData, setPropertyData] = React.useState({});
  const [groupPickerOpen, setGroupPickerOpen] = React.useState(false);
  const [groupOverrides, setGroupOverrides] = React.useState({});
  const groupPickerRef = React.useRef(null);
  const [groupActiveIdx, setGroupActiveIdx] = React.useState(-1);
  React.useEffect(() => {
    if (!groupPickerOpen) return;
    const onDoc = e => {
      if (groupPickerRef.current && !groupPickerRef.current.contains(e.target)) setGroupPickerOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, [groupPickerOpen]);
  const [posInfoOpen, setPosInfoOpen] = React.useState(false);
  const activeProperty = selected && !selected.startsWith('group:') ? listings.find(l => l.name === selected) : null;
  const propFor = name => propertyData[name] || {
    enabled: true,
    method: 'median',
    manualBase: '',
    positioning: '1',
    minComp: '',
    useUrgency: 'global',
    urgencyOpen: false,
    rules: [{
      f: 0,
      t: 3,
      d: -0.3
    }, {
      f: 4,
      t: 7,
      d: -0.2
    }, {
      f: 8,
      t: 14,
      d: -0.1
    }, {
      f: 15,
      t: 30,
      d: -0.05
    }],
    minIDR: '',
    maxIDR: '',
    step: ''
  };
  const setPropField = (name, field, val) => setPropertyData(d => ({
    ...d,
    [name]: {
      ...propFor(name),
      [field]: val
    }
  }));
  const setPropRules = (name, updater) => setPropertyData(d => {
    const cur = propFor(name);
    const rules = typeof updater === 'function' ? updater(cur.rules) : updater;
    return {
      ...d,
      [name]: {
        ...cur,
        rules
      }
    };
  });
  const saveProperty = name => {
    setToast('Property settings saved.');
    setTimeout(() => setToast(null), 2600);
    setSelected(null);
  };
  const [groupData, setGroupData] = React.useState({});
  const defaultGroupUrls = gname => Array.from({
    length: 9
  }, (_, i) => `https://www.airbnb.com/rooms/${1500000000000 + Math.abs(Math.round(Math.sin(gname.length + i * 3.1) * 99999999999))}`).join('\n');
  const activeGroupName = selected && selected.startsWith('group:') ? selected.slice(6) : null;
  const groupFor = gname => groupData[gname] || {
    name: gname,
    minComp: '',
    urls: defaultGroupUrls(gname)
  };
  const setGroupField = (gname, field, val) => setGroupData(d => ({
    ...d,
    [gname]: {
      ...groupFor(gname),
      [field]: val
    }
  }));
  const saveGroup = gname => {
    setToast('Pricing group saved.');
    setTimeout(() => setToast(null), 2600);
    setSelected(null);
  };
  const scrollRef = React.useRef(null);
  const [canLeft, setCanLeft] = React.useState(false);
  const [canRight, setCanRight] = React.useState(true);
  const [currentMonth, setCurrentMonth] = React.useState(0);
  const colWidth = 96;
  const labelColWidth = 280;
  const months = [];
  days.forEach((d, i) => {
    if (i === 0 || d.getDate() === 1) months.push({
      label: monthLabel(d),
      start: i
    });
  });
  const updateHoverFromPointer = (x, y) => {
    const el = document.elementFromPoint(x, y);
    const cellEl = el && el.closest && el.closest('[data-cell-key]');
    if (!cellEl) {
      setHoverCellKey(null);
      setTooltipData(null);
      return;
    }
    setHoverCellKey(cellEl.getAttribute('data-cell-key'));
    const diff = Number(cellEl.getAttribute('data-diff') || 0);
    const breakdownStr = cellEl.getAttribute('data-breakdown');
    if (!diff || !breakdownStr) {
      setTooltipData(null);
      return;
    }
    const cur = Number(cellEl.getAttribute('data-cur') || 0);
    const breakdown = JSON.parse(breakdownStr);
    const rect = cellEl.getBoundingClientRect();
    const placeBelow = rect.top < 320;
    const left = Math.min(Math.max(rect.left + rect.width / 2, 140), window.innerWidth - 140);
    setTooltipData({
      left,
      top: placeBelow ? rect.bottom + 8 : rect.top - 8,
      placeBelow,
      diff,
      cur,
      breakdown
    });
  };
  const updateScrollState = () => {
    const el = scrollRef.current;
    if (!el) return;
    updateHoverFromPointer(lastPointer.current.x, lastPointer.current.y);
    setCanLeft(el.scrollLeft > 4);
    setCanRight(el.scrollLeft < el.scrollWidth - el.clientWidth - 4);
    const visibleCol = Math.round(el.scrollLeft / colWidth);
    let mi = 0;
    months.forEach((m, idx) => {
      if (visibleCol >= m.start) mi = idx;
    });
    setCurrentMonth(mi);
  };
  React.useEffect(() => {
    updateScrollState();
  }, []);
  const scrollBy = dir => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollBy({
      left: dir * colWidth * 4,
      behavior: 'smooth'
    });
    setTimeout(updateScrollState, 300);
  };
  const scrollToCol = colIdx => {
    const el = scrollRef.current;
    if (!el) return;
    el.scrollTo({
      left: colIdx * colWidth,
      behavior: 'smooth'
    });
    setTimeout(updateScrollState, 350);
  };
  const scrollToToday = () => scrollToCol(0);
  const price = (base, i) => Math.round((base + Math.sin(i * 1.7) * base * 0.06 + (i % 5 === 0 ? base * 0.18 : 0)) / 1000) * 1000;
  const fmtRp = n => 'Rp ' + Math.round(n).toLocaleString('id-ID');
  const buildBreakdown = (base, i, li, cur) => {
    const seed = Math.sin(i * 3.1 + li * 5.7);
    const guestMedian = Math.round(base * (0.75 + 0.35 * Math.abs(Math.sin(i * 2.1 + li * 1.3))));
    const hasCompetitorData = Math.abs(Math.sin(i * 0.9 + li)) > 0.15;
    const requiredComp = 3;
    const availableComp = hasCompetitorData ? 1 + Math.floor(Math.abs(Math.sin(i * 1.3 + li * 0.7)) * 3) : null;
    const guestToHostFactor = +(0.75 + 0.2 * Math.abs(Math.cos(i * 0.5 + li))).toFixed(3);
    const hostMedian = Math.round(guestMedian * guestToHostFactor);
    const positioningApplies = Math.abs(Math.sin(i * 0.4 + li * 1.9)) > 0.1;
    const positioningFactor = positioningApplies ? +(0.9 + 0.2 * Math.abs(Math.sin(i * 0.3 + li * 2))).toFixed(2) : null;
    const basePrice = Math.round(hostMedian * (positioningFactor == null ? 1 : positioningFactor));
    const urgencyApplies = i <= 14;
    const urgencyPct = urgencyApplies ? +(seed * 30).toFixed(1) : null;
    const raw = urgencyApplies ? Math.round(basePrice * (1 + urgencyPct / 100)) : basePrice;
    const rounded = Math.round(raw / 1000) * 1000;
    const dateOverride = Math.abs(Math.sin(i * 4.4 + li * 3.3)) > 0.93;
    const final = dateOverride ? cur : rounded;
    return {
      source: 'airbnb_market_median',
      guestMedian,
      availableComp,
      requiredComp,
      guestToHostFactor,
      hostMedian,
      positioningFactor,
      basePrice,
      daysUntilStay: urgencyApplies ? i : null,
      urgencyPct,
      raw,
      rounded,
      final,
      dateOverride
    };
  };
  const recommendation = (base, i, li) => {
    const cur = price(base, i);
    const breakdown = buildBreakdown(base, i, li, cur);
    const rec = breakdown.final;
    if (rec === cur) return {
      rec: cur,
      breakdown: null
    };
    return {
      rec,
      breakdown
    };
  };
  const runAction = (key, label) => {
    setBusy(key);
    setTimeout(() => {
      setBusy(null);
      setToast(label);
      if (key === 'fetch') setLastSync(s => ({
        ...s,
        fetch: 'Just now'
      }));
      if (key === 'comp') setLastSync(s => ({
        ...s,
        comp: 'Just now'
      }));
      if (key === 'generate') setLastSync(s => ({
        ...s,
        generate: 'Just now'
      }));
      if (key === 'apply') setLastSync(s => ({
        ...s,
        apply: 'Just now'
      }));
      setTimeout(() => setToast(null), 2600);
    }, 900);
  };
  const handleCellClick = (propIndex, dayIndex) => {
    if (!rangeAnchor) {
      setRangeAnchor({
        propIndex,
        dayIndex
      });
      setRangeSelection({
        minProp: propIndex,
        maxProp: propIndex,
        minDay: dayIndex,
        maxDay: dayIndex
      });
    } else {
      setRangeSelection({
        minProp: Math.min(rangeAnchor.propIndex, propIndex),
        maxProp: Math.max(rangeAnchor.propIndex, propIndex),
        minDay: Math.min(rangeAnchor.dayIndex, dayIndex),
        maxDay: Math.max(rangeAnchor.dayIndex, dayIndex)
      });
      setRangeAnchor(null);
    }
  };
  const clearRange = () => {
    setRangeAnchor(null);
    setRangeSelection(null);
    setRangePriceInput('');
  };
  const saveRangePrice = () => {
    const val = Number(String(rangePriceInput).replace(/[^0-9]/g, ''));
    if (!val || !rangeSelection) return;
    const updates = {};
    listings.forEach(l => {
      if (l.propIndex < rangeSelection.minProp || l.propIndex > rangeSelection.maxProp) return;
      for (let i = rangeSelection.minDay; i <= rangeSelection.maxDay; i++) {
        updates[l.name + '-' + i] = val;
      }
    });
    setPriceOverrides(o => ({
      ...o,
      ...updates
    }));
    const nDates = (rangeSelection.maxDay - rangeSelection.minDay + 1) * (rangeSelection.maxProp - rangeSelection.minProp + 1);
    setToast(`Price updated for ${nDates} date${nDates === 1 ? '' : 's'}.`);
    setTimeout(() => setToast(null), 2600);
    clearRange();
  };
  const dateLabel = d => d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric'
  });
  const cols = `${labelColWidth}px repeat(${days.length},${colWidth}px)`;
  return /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      display: 'flex',
      flexDirection: 'column',
      minWidth: 0,
      background: 'var(--color-white)',
      position: 'relative',
      zIndex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      rowGap: 12,
      padding: '20px 24px',
      borderBottom: '1px solid var(--border-default)'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(Select, {
    value: String(currentMonth),
    pill: true,
    onChange: e => scrollToCol(months[Number(e.target.value)].start),
    options: months.map((m, idx) => ({
      label: m.label,
      value: String(idx)
    }))
  }), /*#__PURE__*/React.createElement("div", {
    onClick: scrollToToday,
    style: {
      padding: '0 16px',
      height: 38,
      boxSizing: 'border-box',
      display: 'flex',
      alignItems: 'center',
      borderRadius: 'var(--radius-full)',
      border: '1px solid var(--border-default)',
      fontSize: 13,
      fontWeight: 600,
      cursor: 'pointer'
    }
  }, "Today")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      gap: 8
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    onClick: () => setGlobalOpen(true)
  }, "Global settings"), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    onClick: () => setActionsOpen(true)
  }, "Actions"))), toast && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      top: 20,
      right: 24,
      zIndex: 20
    }
  }, /*#__PURE__*/React.createElement(Toast, {
    tone: "success",
    onClose: () => setToast(null)
  }, toast)), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      position: 'relative',
      minHeight: 0,
      minWidth: 0
    }
  }, /*#__PURE__*/React.createElement("div", {
    ref: scrollRef,
    onScroll: updateScrollState,
    onMouseMove: e => {
      lastPointer.current = {
        x: e.clientX,
        y: e.clientY
      };
      updateHoverFromPointer(e.clientX, e.clientY);
    },
    onMouseLeave: () => {
      setHoverCellKey(null);
      setTooltipData(null);
    },
    style: {
      height: '100%',
      overflow: 'auto'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: cols,
      minWidth: 'fit-content'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      gridColumn: '1',
      gridRow: 1,
      position: 'sticky',
      left: 0,
      top: 0,
      zIndex: 4,
      background: 'var(--color-white)',
      padding: '20px 20px 12px',
      height: 48,
      boxSizing: 'border-box',
      display: 'flex',
      alignItems: 'center'
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: 'var(--text-lg)',
      fontWeight: 600,
      margin: 0
    }
  }, listings.length, " Properties")), months.map((m, idx) => /*#__PURE__*/React.createElement("div", {
    key: m.label,
    style: {
      gridColumn: `${m.start + 2} / ${idx + 1 < months.length ? months[idx + 1].start + 2 : days.length + 2}`,
      gridRow: 1,
      position: 'sticky',
      top: 0,
      left: labelColWidth,
      height: 48,
      boxSizing: 'border-box',
      zIndex: 2,
      background: 'var(--color-white)',
      padding: '14px 16px',
      fontFamily: 'var(--font-display)',
      fontWeight: 600,
      fontSize: 15,
      width: 'fit-content',
      maxWidth: '100%',
      whiteSpace: 'nowrap'
    }
  }, m.label)), /*#__PURE__*/React.createElement("div", {
    style: {
      gridColumn: '1',
      gridRow: 2,
      position: 'sticky',
      left: 0,
      top: 48,
      zIndex: 4,
      background: 'var(--color-white)',
      borderBottom: '1px solid var(--border-default)',
      padding: '0 20px 12px'
    }
  }, /*#__PURE__*/React.createElement(Input, {
    placeholder: "Search listings..."
  })), days.map((d, i) => /*#__PURE__*/React.createElement("div", {
    key: i,
    style: {
      gridColumn: i + 2,
      gridRow: 2,
      position: 'sticky',
      top: 48,
      zIndex: 2,
      background: 'var(--color-white)',
      textAlign: 'center',
      padding: '10px 4px',
      fontSize: 12,
      color: 'var(--text-secondary)',
      borderTop: '1px solid var(--border-default)',
      borderBottom: '1px solid var(--border-default)'
    }
  }, /*#__PURE__*/React.createElement("div", null, d.toLocaleDateString('en-US', {
    weekday: 'narrow'
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 600,
      color: 'var(--text-primary)',
      marginTop: 2
    }
  }, d.getDate()))), months.filter((m, idx) => idx > 0).map(m => /*#__PURE__*/React.createElement("div", {
    key: 'div-' + m.label,
    style: {
      gridColumn: m.start + 2,
      gridRow: '1 / 3',
      zIndex: 3,
      borderLeft: '1px solid var(--border-default)',
      pointerEvents: 'none'
    }
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      gridColumn: 1,
      gridRow: `1 / ${totalRows}`,
      position: 'sticky',
      left: labelColWidth,
      width: 0,
      zIndex: 5,
      borderRight: '1px solid var(--border-default)',
      pointerEvents: 'none'
    }
  }), groups.map(g => {
    const headerRow = g.row;
    const [groupHover, setGroupHover] = React.useState(false);
    return /*#__PURE__*/React.createElement(React.Fragment, {
      key: g.name
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        gridColumn: '1',
        gridRow: headerRow,
        position: 'sticky',
        left: 0,
        top: 96,
        zIndex: 5,
        boxSizing: 'border-box'
      }
    }, /*#__PURE__*/React.createElement("div", {
      onClick: () => setSelected('group:' + g.name),
      onMouseEnter: () => setGroupHover(true),
      onMouseLeave: () => setGroupHover(false),
      style: {
        width: labelColWidth,
        height: '100%',
        boxSizing: 'border-box',
        display: 'flex',
        alignItems: 'center',
        padding: '10px 20px',
        cursor: 'pointer',
        background: selected === 'group:' + g.name ? 'var(--surface-sunken)' : groupHover ? 'rgba(11,12,14,0.05)' : 'var(--color-mist)',
        borderBottom: '1px solid var(--border-default)',
        borderTop: '1px solid var(--border-default)'
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontWeight: 700,
        fontSize: 13,
        color: 'var(--text-primary)'
      }
    }, g.name))), /*#__PURE__*/React.createElement("div", {
      style: {
        gridColumn: '2 / -1',
        gridRow: headerRow,
        position: 'sticky',
        top: 96,
        background: 'var(--color-mist)',
        borderBottom: '1px solid var(--border-default)',
        borderTop: '1px solid var(--border-default)',
        boxSizing: 'border-box',
        zIndex: 4
      }
    }), g.items.map((l, li) => {
      const [hover, setHover] = React.useState(false);
      return /*#__PURE__*/React.createElement(React.Fragment, {
        key: l.name
      }, /*#__PURE__*/React.createElement("div", {
        onClick: () => setSelected(l.name),
        onMouseEnter: () => setHover(true),
        onMouseLeave: () => setHover(false),
        style: {
          gridColumn: '1',
          gridRow: l.row,
          position: 'sticky',
          left: 0,
          zIndex: 3,
          background: selected === l.name ? 'var(--surface-sunken)' : hover ? 'var(--color-mist)' : 'var(--color-white)',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
          padding: '12px 20px',
          borderBottom: '1px solid var(--border-default)',
          cursor: 'pointer',
          transition: 'background var(--duration-fast) var(--ease-standard)'
        }
      }, /*#__PURE__*/React.createElement("div", {
        style: {
          width: 44,
          height: 44,
          borderRadius: 'var(--radius-md)',
          background: l.c,
          flexShrink: 0
        }
      }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
        style: {
          fontWeight: 600,
          fontSize: 14,
          color: 'var(--text-primary)'
        }
      }, l.name), /*#__PURE__*/React.createElement("div", {
        style: {
          fontSize: 12,
          color: 'var(--text-secondary)'
        }
      }, "IDR (Rp)"))), days.map((d, i) => {
        const cur = priceOverrides[l.name + '-' + i] ?? price(l.base, i);
        const {
          rec,
          breakdown
        } = recommendation(l.base, i, li);
        const diff = rec - cur;
        const cellKey = l.name + '-' + i;
        const isHover = hoverCellKey === cellKey;
        const inRange = rangeSelection && l.propIndex >= rangeSelection.minProp && l.propIndex <= rangeSelection.maxProp && i >= rangeSelection.minDay && i <= rangeSelection.maxDay;
        const isAnchor = rangeAnchor && rangeAnchor.propIndex === l.propIndex && rangeAnchor.dayIndex === i;
        const edgeTop = (isAnchor || inRange) && l.propIndex === (rangeSelection ? rangeSelection.minProp : l.propIndex);
        const edgeBottom = (isAnchor || inRange) && l.propIndex === (rangeSelection ? rangeSelection.maxProp : l.propIndex);
        const edgeLeft = (isAnchor || inRange) && i === (rangeSelection ? rangeSelection.minDay : i);
        const edgeRight = (isAnchor || inRange) && i === (rangeSelection ? rangeSelection.maxDay : i);
        const cellBg = isAnchor ? 'var(--action-accent-soft)' : inRange ? 'rgba(207,242,17,0.16)' : isHover ? 'rgba(11,12,14,0.04)' : selected === l.name ? 'var(--surface-sunken)' : 'var(--color-white)';
        return /*#__PURE__*/React.createElement("div", {
          key: i,
          onClick: () => handleCellClick(l.propIndex, i),
          "data-cell-key": cellKey,
          "data-diff": diff,
          "data-cur": cur,
          "data-breakdown": breakdown ? JSON.stringify(breakdown) : '',
          style: {
            gridColumn: i + 2,
            gridRow: l.row,
            position: 'relative',
            padding: '14px 8px',
            textAlign: 'right',
            fontFamily: 'var(--font-sans)',
            fontVariantNumeric: 'tabular-nums',
            fontSize: 12.5,
            color: 'var(--text-primary)',
            background: cellBg,
            borderTop: edgeTop ? '1.5px solid var(--color-accent-500)' : 'none',
            borderBottom: edgeBottom ? '1.5px solid var(--color-accent-500)' : '1px solid var(--border-default)',
            borderLeft: edgeLeft ? '1.5px solid var(--color-accent-500)' : d.getDate() === 1 ? '1px solid var(--border-default)' : 'none',
            borderRight: edgeRight ? '1.5px solid var(--color-accent-500)' : 'none',
            cursor: 'pointer',
            transition: 'background var(--duration-fast) var(--ease-standard)'
          }
        }, /*#__PURE__*/React.createElement("div", null, cur.toLocaleString('en-US')), diff !== 0 && /*#__PURE__*/React.createElement("div", {
          style: {
            marginTop: 2,
            fontSize: 11,
            fontWeight: 600,
            color: diff > 0 ? 'var(--status-success)' : 'var(--status-danger)'
          }
        }, rec.toLocaleString('en-US')));
      }));
    }));
  }))), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: labelColWidth,
      top: 0,
      bottom: 0,
      width: 32,
      background: 'linear-gradient(to right, rgba(11,12,14,0.10), rgba(11,12,14,0))',
      pointerEvents: 'none',
      opacity: canLeft ? 1 : 0,
      transition: 'opacity var(--duration-standard) var(--ease-standard)',
      zIndex: 5
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      right: 0,
      top: 0,
      bottom: 0,
      width: 32,
      background: 'linear-gradient(to left, rgba(11,12,14,0.10), rgba(11,12,14,0))',
      pointerEvents: 'none',
      opacity: canRight ? 1 : 0,
      transition: 'opacity var(--duration-standard) var(--ease-standard)',
      zIndex: 5
    }
  }), canLeft && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      left: labelColWidth + 8,
      top: 76,
      transform: 'translateY(-50%)',
      zIndex: 6
    }
  }, /*#__PURE__*/React.createElement(IconButton, {
    label: "Scroll earlier",
    onClick: () => scrollBy(-1),
    icon: /*#__PURE__*/React.createElement("img", {
      src: "https://unpkg.com/lucide-static@latest/icons/chevron-left.svg",
      style: {
        width: 16,
        height: 16
      }
    })
  })), canRight && /*#__PURE__*/React.createElement("div", {
    style: {
      position: 'absolute',
      right: 8,
      top: 76,
      transform: 'translateY(-50%)',
      zIndex: 6
    }
  }, /*#__PURE__*/React.createElement(IconButton, {
    label: "Scroll later",
    onClick: () => scrollBy(1),
    icon: /*#__PURE__*/React.createElement("img", {
      src: "https://unpkg.com/lucide-static@latest/icons/chevron-right.svg",
      style: {
        width: 16,
        height: 16
      }
    })
  })), tooltipData && ReactDOM.createPortal(/*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      left: tooltipData.left,
      top: tooltipData.top,
      transform: `translate(-50%, ${tooltipData.placeBelow ? '0' : '-100%'})`,
      width: 264,
      background: 'var(--color-ink-600)',
      color: '#fff',
      fontSize: 11.5,
      lineHeight: 1.5,
      padding: '12px 14px',
      borderRadius: 'var(--radius-sm)',
      fontFamily: 'var(--font-sans)',
      zIndex: 1000,
      boxShadow: 'var(--shadow-md)',
      textAlign: 'left',
      pointerEvents: 'none'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      marginBottom: 8,
      fontSize: 13,
      color: tooltipData.diff > 0 ? '#8fe8bd' : '#ffb4b4'
    }
  }, tooltipData.diff > 0 ? '+' : '-', "Rp", Math.abs(tooltipData.diff).toLocaleString('en-US'), " (", tooltipData.diff > 0 ? '+' : '-', Math.abs(Math.round(tooltipData.diff / tooltipData.cur * 100)), "%)"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 3
    }
  }, [['Price source', tooltipData.breakdown.source], ['Airbnb guest median', fmtRp(tooltipData.breakdown.guestMedian)], tooltipData.breakdown.availableComp != null && ['Available / required competitors', `${tooltipData.breakdown.availableComp} / ${tooltipData.breakdown.requiredComp}`], ['Guest-to-host factor', tooltipData.breakdown.guestToHostFactor], ['Estimated host median', fmtRp(tooltipData.breakdown.hostMedian)], tooltipData.breakdown.positioningFactor != null && ['Positioning factor', tooltipData.breakdown.positioningFactor], ['Base price', fmtRp(tooltipData.breakdown.basePrice)], tooltipData.breakdown.daysUntilStay != null && ['Days until stay', tooltipData.breakdown.daysUntilStay], tooltipData.breakdown.urgencyPct != null && ['Urgency adjustment', `${tooltipData.breakdown.urgencyPct > 0 ? '+' : ''}${tooltipData.breakdown.urgencyPct.toFixed(1)}%`], ['Raw / rounded / final', `${fmtRp(tooltipData.breakdown.raw)} / ${fmtRp(tooltipData.breakdown.rounded)} / ${fmtRp(tooltipData.breakdown.final)}`], ['Date override', tooltipData.breakdown.dateOverride ? 'Yes' : 'No']].filter(Boolean).map(([k, v]) => /*#__PURE__*/React.createElement("div", {
    key: k,
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'rgba(255,255,255,0.6)'
    }
  }, k), /*#__PURE__*/React.createElement("span", {
    style: {
      fontWeight: 600,
      textAlign: 'right'
    }
  }, v))))), document.body), ReactDOM.createPortal(/*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      top: 0,
      right: 0,
      height: '100vh',
      width: 300,
      background: 'var(--color-white)',
      boxShadow: actionsOpen ? 'var(--shadow-lg)' : 'none',
      borderLeft: '1px solid var(--border-default)',
      transform: `translateX(${actionsOpen ? '0' : '100%'})`,
      transition: 'transform var(--duration-standard) var(--ease-standard)',
      zIndex: 201,
      display: 'flex',
      flexDirection: 'column',
      padding: 24,
      boxSizing: 'border-box'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 20
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: 'var(--text-lg)',
      fontWeight: 600,
      margin: 0
    }
  }, "Actions"), /*#__PURE__*/React.createElement(IconButton, {
    label: "Close",
    onClick: () => setActionsOpen(false),
    icon: /*#__PURE__*/React.createElement("img", {
      src: "https://unpkg.com/lucide-static@latest/icons/x.svg",
      style: {
        width: 16,
        height: 16
      }
    })
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    style: {
      width: '100%'
    },
    onClick: () => runAction('fetch', 'Prices fetched from your channels.'),
    disabled: busy === 'fetch'
  }, busy === 'fetch' ? 'Fetching…' : 'Fetch current prices'), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--text-muted)',
      textAlign: 'center'
    }
  }, "Last fetched: ", lastSync.fetch)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    style: {
      width: '100%'
    },
    onClick: () => runAction('comp', 'Competitor data refreshed.'),
    disabled: busy === 'comp'
  }, busy === 'comp' ? 'Refreshing…' : 'Refresh competitor data'), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--text-muted)',
      textAlign: 'center'
    }
  }, "Last refreshed: ", lastSync.comp)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm",
    style: {
      width: '100%'
    },
    onClick: () => runAction('generate', 'Price recommendations generated.'),
    disabled: busy === 'generate'
  }, busy === 'generate' ? 'Generating…' : 'Generate price recommendations'), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--text-muted)',
      textAlign: 'center'
    }
  }, "Last generated: ", lastSync.generate)), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 4
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "accent",
    size: "sm",
    style: {
      width: '100%'
    },
    onClick: () => runAction('apply', 'Prices applied to your calendar.'),
    disabled: busy === 'apply'
  }, busy === 'apply' ? 'Applying…' : 'Apply prices'), /*#__PURE__*/React.createElement("span", {
    style: {
      fontSize: 11,
      color: 'var(--text-muted)',
      textAlign: 'center'
    }
  }, "Last applied: ", lastSync.apply)))), document.body), ReactDOM.createPortal(/*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      top: 0,
      right: 0,
      height: '100vh',
      width: 300,
      background: 'var(--color-white)',
      boxShadow: rangeSelection && !rangeAnchor ? 'var(--shadow-lg)' : 'none',
      borderLeft: '1px solid var(--border-default)',
      transform: `translateX(${rangeSelection && !rangeAnchor ? '0' : '100%'})`,
      transition: 'transform var(--duration-standard) var(--ease-standard)',
      zIndex: 202,
      display: 'flex',
      flexDirection: 'column',
      padding: 24,
      boxSizing: 'border-box'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      marginBottom: 20,
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", null, rangeSelection && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 16,
      fontWeight: 600,
      color: 'var(--text-primary)',
      marginBottom: 4
    }
  }, dateLabel(days[rangeSelection.minDay]), " \u2013 ", dateLabel(days[rangeSelection.maxDay])), rangeSelection && /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 14,
      color: 'var(--text-secondary)'
    }
  }, rangeSelection.maxProp - rangeSelection.minProp + 1, " propert", rangeSelection.maxProp - rangeSelection.minProp + 1 === 1 ? 'y' : 'ies', " selected")), /*#__PURE__*/React.createElement(IconButton, {
    label: "Close",
    onClick: clearRange,
    icon: /*#__PURE__*/React.createElement("img", {
      src: "https://unpkg.com/lucide-static@latest/icons/x.svg",
      style: {
        width: 16,
        height: 16
      }
    })
  })), /*#__PURE__*/React.createElement(Input, {
    label: "Nightly price",
    prefix: "Rp",
    placeholder: "e.g. 4,500,000",
    value: rangePriceInput,
    onChange: e => setRangePriceInput(e.target.value)
  }), /*#__PURE__*/React.createElement(Button, {
    variant: "accent",
    size: "sm",
    style: {
      width: '100%',
      marginTop: 16
    },
    onClick: saveRangePrice
  }, "Save")), document.body), ReactDOM.createPortal(/*#__PURE__*/React.createElement("div", {
    onClick: () => setGlobalOpen(false),
    style: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(11,12,14,0.28)',
      backdropFilter: 'blur(2px)',
      opacity: globalOpen ? 1 : 0,
      pointerEvents: globalOpen ? 'auto' : 'none',
      transition: 'opacity var(--duration-standard) var(--ease-standard)',
      zIndex: 207
    }
  }), document.body), ReactDOM.createPortal(/*#__PURE__*/React.createElement("div", {
    style: {
      position: 'fixed',
      top: 0,
      right: 0,
      height: '100vh',
      width: 460,
      background: 'var(--color-white)',
      boxShadow: globalOpen ? 'var(--shadow-lg)' : 'none',
      borderLeft: '1px solid var(--border-default)',
      transform: `translateX(${globalOpen ? '0' : '100%'})`,
      transition: 'transform var(--duration-standard) var(--ease-standard)',
      zIndex: 208,
      display: 'flex',
      flexDirection: 'column'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '24px 28px 20px',
      borderBottom: '1px solid var(--border-default)',
      display: 'flex',
      alignItems: 'flex-start',
      justifyContent: 'space-between',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-display)',
      fontSize: 20,
      fontWeight: 600,
      color: 'var(--text-primary)'
    }
  }, "Global settings"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 12,
      color: 'var(--text-secondary)',
      marginTop: 4
    }
  }, "Defaults every group and property inherit from")), /*#__PURE__*/React.createElement(IconButton, {
    label: "Close",
    onClick: () => setGlobalOpen(false),
    icon: /*#__PURE__*/React.createElement("img", {
      src: "https://unpkg.com/lucide-static@latest/icons/x.svg",
      style: {
        width: 16,
        height: 16
      }
    })
  })), /*#__PURE__*/React.createElement("div", {
    style: {
      flex: 1,
      overflow: 'auto',
      padding: '20px 28px',
      display: 'flex',
      flexDirection: 'column',
      gap: 20
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(Input, {
    label: "Guest-to-host factor",
    value: globalSettings.guestToHost,
    onChange: e => setGlobalField('guestToHost', e.target.value)
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 11.5,
      color: 'var(--text-muted)',
      marginTop: 6
    }
  }, "Converts Airbnb guest median to estimated host revenue.")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      fontSize: 13,
      color: 'var(--text-primary)',
      marginBottom: 12
    }
  }, "Base price"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      gap: 0,
      background: 'var(--surface-sunken)',
      borderRadius: 'var(--radius-md)',
      padding: 3
    }
  }, [{
    label: 'Market median',
    value: 'median'
  }, {
    label: 'Manual',
    value: 'manual'
  }].map(o => /*#__PURE__*/React.createElement("div", {
    key: o.value,
    onClick: () => setGlobalField('method', o.value),
    style: {
      flex: 1,
      textAlign: 'center',
      padding: '7px 0',
      borderRadius: 'var(--radius-sm)',
      fontSize: 12.5,
      fontWeight: 600,
      cursor: 'pointer',
      background: globalSettings.method === o.value ? 'var(--color-white)' : 'transparent',
      color: globalSettings.method === o.value ? 'var(--text-primary)' : 'var(--text-secondary)',
      boxShadow: globalSettings.method === o.value ? 'var(--shadow-sm)' : 'none',
      transition: 'background var(--duration-fast) var(--ease-standard)'
    }
  }, o.label))), globalSettings.method === 'manual' && /*#__PURE__*/React.createElement(Input, {
    label: "Manual base price",
    placeholder: "Example: 4,500,000",
    value: globalSettings.manualBase,
    onChange: e => setGlobalField('manualBase', e.target.value)
  }), globalSettings.method === 'median' && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement(Input, {
    label: "Market positioning factor",
    value: globalSettings.positioning,
    onChange: e => setGlobalField('positioning', e.target.value)
  }), /*#__PURE__*/React.createElement(Input, {
    label: "Minimum competitor count",
    value: globalSettings.minComp,
    onChange: e => setGlobalField('minComp', e.target.value)
  })))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      marginBottom: 14
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      fontSize: 13,
      color: 'var(--text-primary)'
    }
  }, "Discounts by days left until stay"), /*#__PURE__*/React.createElement(Switch, {
    checked: globalSettings.useUrgency !== 'off',
    onChange: v => setGlobalField('useUrgency', v ? 'on' : 'off')
  })), globalSettings.useUrgency !== 'off' && /*#__PURE__*/React.createElement(UrgencyRulesEditor, {
    rules: globalSettings.rules,
    setRules: u => setGlobalSettings(s => ({
      ...s,
      rules: typeof u === 'function' ? u(s.rules) : u
    }))
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontWeight: 700,
      fontSize: 13,
      color: 'var(--text-primary)',
      marginBottom: 12
    }
  }, "Bounds and rounding"), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement(Input, {
    label: "Minimum price",
    value: globalSettings.minIDR,
    onChange: e => setGlobalField('minIDR', e.target.value)
  }), /*#__PURE__*/React.createElement(Input, {
    label: "Maximum price",
    value: globalSettings.maxIDR,
    onChange: e => setGlobalField('maxIDR', e.target.value)
  })), /*#__PURE__*/React.createElement(Input, {
    label: "Round to nearest",
    value: globalSettings.step,
    onChange: e => setGlobalField('step', e.target.value)
  })))), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '16px 28px',
      borderTop: '1px solid var(--border-default)',
      display: 'flex',
      gap: 10
    }
  }, /*#__PURE__*/React.createElement(Button, {
    variant: "accent",
    size: "sm",
    style: {
      width: '100%'
    },
    onClick: saveGlobal
  }, "Save"))), document.body), ReactDOM.createPortal(/*#__PURE__*/React.createElement("div", {
    onClick: () => setSelected(null),
    style: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(11,12,14,0.28)',
      backdropFilter: 'blur(2px)',
      opacity: activeGroupName ? 1 : 0,
      pointerEvents: activeGroupName ? 'auto' : 'none',
      transition: 'opacity var(--duration-standard) var(--ease-standard)',
      zIndex: 203
    }
  }), document.body), ReactDOM.createPortal((() => {
    const g = activeGroupName ? groups.find(x => x.name === activeGroupName) : null;
    const gd = activeGroupName ? groupFor(activeGroupName) : null;
    return /*#__PURE__*/React.createElement("div", {
      style: {
        position: 'fixed',
        top: 0,
        right: 0,
        height: '100vh',
        width: 400,
        background: 'var(--color-white)',
        boxShadow: activeGroupName ? 'var(--shadow-lg)' : 'none',
        borderLeft: '1px solid var(--border-default)',
        transform: `translateX(${activeGroupName ? '0' : '100%'})`,
        transition: 'transform var(--duration-standard) var(--ease-standard)',
        zIndex: 204,
        display: 'flex',
        flexDirection: 'column'
      }
    }, g && gd && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      style: {
        padding: '24px 28px 20px',
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: 12
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        minWidth: 0
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11,
        fontWeight: 700,
        letterSpacing: '0.04em',
        textTransform: 'uppercase',
        color: 'var(--text-muted)',
        marginBottom: 6
      }
    }, "Pricing group"), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 8
      }
    }, /*#__PURE__*/React.createElement("input", {
      value: gd.name,
      onChange: e => setGroupField(g.name, 'name', e.target.value),
      style: {
        fontFamily: 'var(--font-display)',
        fontSize: 22,
        fontWeight: 600,
        color: 'var(--text-primary)',
        border: 'none',
        outline: 'none',
        background: 'transparent',
        padding: 0,
        minWidth: 0,
        flex: '0 1 auto',
        borderRadius: 'var(--radius-sm)'
      },
      onFocus: e => e.target.style.background = 'var(--color-mist)',
      onBlur: e => e.target.style.background = 'transparent'
    }), /*#__PURE__*/React.createElement("img", {
      src: "https://unpkg.com/lucide-static@latest/icons/pencil.svg",
      style: {
        width: 14,
        height: 14,
        opacity: 0.35,
        flexShrink: 0
      }
    }))), /*#__PURE__*/React.createElement(IconButton, {
      label: "Close",
      onClick: () => setSelected(null),
      icon: /*#__PURE__*/React.createElement("img", {
        src: "https://unpkg.com/lucide-static@latest/icons/x.svg",
        style: {
          width: 16,
          height: 16
        }
      })
    })), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        overflow: 'auto',
        padding: '20px 28px',
        display: 'flex',
        flexDirection: 'column',
        gap: 20
      }
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 12,
        fontWeight: 600,
        color: 'var(--text-secondary)',
        marginBottom: 8
      }
    }, "Properties in this group"), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        flexWrap: 'wrap',
        gap: 8
      }
    }, g.items.map(it => /*#__PURE__*/React.createElement("div", {
      key: it.name,
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        padding: '6px 12px 6px 6px',
        borderRadius: 'var(--radius-full)',
        background: 'var(--color-mist)',
        border: '1px solid var(--border-default)'
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        width: 20,
        height: 20,
        borderRadius: '50%',
        background: it.c,
        flexShrink: 0
      }
    }), /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        fontWeight: 600,
        color: 'var(--text-primary)'
      }
    }, it.name))))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement(InputWithSelectField, {
      label: "Minimum competitor count",
      value: gd.minComp,
      onChange: v => setGroupField(g.name, 'minComp', v),
      options: [{
        label: 'Global: ' + globalSettings.minComp,
        value: '',
        linked: true
      }]
    }), /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 11.5,
        color: 'var(--text-muted)',
        marginTop: 6
      }
    }, "Threshold for refreshing the saved market median.")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        fontSize: 13,
        fontWeight: 600,
        color: 'var(--text-primary)',
        marginBottom: 8
      }
    }, "Competitor URLs"), /*#__PURE__*/React.createElement("textarea", {
      value: gd.urls,
      onChange: e => setGroupField(g.name, 'urls', e.target.value),
      rows: 9,
      style: {
        width: '100%',
        boxSizing: 'border-box',
        resize: 'vertical',
        fontFamily: 'var(--font-sans)',
        fontSize: 12,
        lineHeight: 1.7,
        color: 'var(--text-primary)',
        padding: '12px 14px',
        borderRadius: 'var(--radius-md)',
        border: '1px solid var(--border-default)',
        outline: 'none'
      }
    }))), /*#__PURE__*/React.createElement("div", {
      style: {
        padding: '16px 28px',
        borderTop: '1px solid var(--border-default)',
        display: 'flex',
        gap: 10
      }
    }, /*#__PURE__*/React.createElement(Button, {
      variant: "accent",
      size: "sm",
      style: {
        width: '100%'
      },
      onClick: () => saveGroup(g.name)
    }, "Save"))));
  })(), document.body), ReactDOM.createPortal(/*#__PURE__*/React.createElement("div", {
    onClick: () => setSelected(null),
    style: {
      position: 'fixed',
      inset: 0,
      background: 'rgba(11,12,14,0.28)',
      backdropFilter: 'blur(2px)',
      opacity: activeProperty ? 1 : 0,
      pointerEvents: activeProperty ? 'auto' : 'none',
      transition: 'opacity var(--duration-standard) var(--ease-standard)',
      zIndex: 205
    }
  }), document.body), ReactDOM.createPortal((() => {
    const l = activeProperty;
    const pd = l ? propFor(l.name) : null;
    return /*#__PURE__*/React.createElement("div", {
      style: {
        position: 'fixed',
        top: 0,
        right: 0,
        height: '100vh',
        width: 460,
        background: 'var(--color-white)',
        boxShadow: activeProperty ? 'var(--shadow-lg)' : 'none',
        borderLeft: '1px solid var(--border-default)',
        transform: `translateX(${activeProperty ? '0' : '100%'})`,
        transition: 'transform var(--duration-standard) var(--ease-standard)',
        zIndex: 206,
        display: 'flex',
        flexDirection: 'column'
      }
    }, l && pd && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      style: {
        padding: '24px 28px 20px',
        borderBottom: '1px solid var(--border-default)',
        display: 'flex',
        alignItems: 'flex-start',
        justifyContent: 'space-between',
        gap: 12
      }
    }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        fontFamily: 'var(--font-display)',
        fontSize: 20,
        fontWeight: 600,
        color: 'var(--text-primary)'
      }
    }, l.name), /*#__PURE__*/React.createElement("div", {
      ref: groupPickerRef,
      style: {
        position: 'relative',
        marginTop: 4
      }
    }, /*#__PURE__*/React.createElement("div", {
      onClick: () => {
        setGroupPickerOpen(o => !o);
        setGroupActiveIdx(-1);
      },
      onKeyDown: e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          setGroupPickerOpen(o => !o);
          setGroupActiveIdx(-1);
        } else if (e.key === 'ArrowDown') {
          e.preventDefault();
          setGroupPickerOpen(true);
          setGroupActiveIdx(i => Math.min(i + 1, groups.length - 1));
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          setGroupActiveIdx(i => Math.max(i - 1, 0));
        } else if (e.key === 'Enter' && groupActiveIdx >= 0) {} else if (e.key === 'Escape') {
          setGroupPickerOpen(false);
        }
      },
      tabIndex: 0,
      role: "button",
      "aria-haspopup": "listbox",
      "aria-expanded": groupPickerOpen,
      style: {
        display: 'inline-flex',
        alignItems: 'center',
        gap: 6,
        cursor: 'pointer',
        padding: '3px 8px',
        margin: '-3px -8px',
        borderRadius: 'var(--radius-sm)',
        outline: 'none',
        transition: 'background var(--duration-fast) var(--ease-standard)'
      },
      onMouseEnter: e => e.currentTarget.style.background = 'rgba(11,12,14,0.05)',
      onMouseLeave: e => e.currentTarget.style.background = 'transparent'
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 14,
        fontWeight: 500,
        color: 'var(--text-primary)'
      }
    }, groupOverrides[l.name] || l.group), /*#__PURE__*/React.createElement("img", {
      src: "https://unpkg.com/lucide-static@latest/icons/pencil.svg",
      style: {
        width: 12,
        height: 12,
        opacity: 0.35
      }
    })), groupPickerOpen && /*#__PURE__*/React.createElement("div", {
      role: "listbox",
      style: {
        position: 'absolute',
        top: 'calc(100% + 6px)',
        left: 0,
        background: 'var(--color-white)',
        border: '1px solid var(--border-default)',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)',
        padding: 6,
        zIndex: 10,
        minWidth: 200,
        maxHeight: 38 * 5,
        overflowY: 'auto'
      }
    }, groups.map((g, gi) => {
      const cur = groupOverrides[l.name] || l.group;
      const isSelected = g.name === cur;
      const isActive = groupActiveIdx === gi;
      return /*#__PURE__*/React.createElement("div", {
        key: g.name,
        role: "option",
        "aria-selected": isSelected,
        onMouseDown: e => {
          e.preventDefault();
          setGroupOverrides(o => ({
            ...o,
            [l.name]: g.name
          }));
          setGroupPickerOpen(false);
        },
        onMouseEnter: () => setGroupActiveIdx(gi),
        style: {
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          height: 36,
          padding: '0 10px',
          borderRadius: 'var(--radius-sm)',
          fontSize: 12.5,
          fontWeight: 600,
          color: isSelected ? 'var(--text-primary)' : 'var(--text-secondary)',
          background: isSelected ? 'var(--color-mist)' : isActive ? 'rgba(11,12,14,0.04)' : 'transparent',
          cursor: 'pointer'
        }
      }, /*#__PURE__*/React.createElement("span", null, g.name), isSelected && /*#__PURE__*/React.createElement("img", {
        src: "https://unpkg.com/lucide-static@latest/icons/check.svg",
        style: {
          width: 13,
          height: 13,
          opacity: 0.6
        }
      }));
    })))), /*#__PURE__*/React.createElement(IconButton, {
      label: "Close",
      onClick: () => setSelected(null),
      icon: /*#__PURE__*/React.createElement("img", {
        src: "https://unpkg.com/lucide-static@latest/icons/x.svg",
        style: {
          width: 16,
          height: 16
        }
      })
    })), /*#__PURE__*/React.createElement("div", {
      style: {
        flex: 1,
        overflow: 'auto',
        padding: '20px 28px',
        display: 'flex',
        flexDirection: 'column',
        gap: 20
      }
    }, /*#__PURE__*/React.createElement(Switch, {
      label: "Suggest pricing",
      checked: pd.enabled,
      onChange: v => setPropField(l.name, 'enabled', v)
    }), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700,
        fontSize: 13,
        color: 'var(--text-primary)',
        marginBottom: 12
      }
    }, "Base price"), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        flexDirection: 'column',
        gap: 12
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        gap: 0,
        background: 'var(--surface-sunken)',
        borderRadius: 'var(--radius-md)',
        padding: 3
      }
    }, [{
      label: 'Market median',
      value: 'median'
    }, {
      label: 'Manual',
      value: 'manual'
    }].map(o => /*#__PURE__*/React.createElement("div", {
      key: o.value,
      onClick: () => setPropField(l.name, 'method', o.value),
      style: {
        flex: 1,
        textAlign: 'center',
        padding: '7px 0',
        borderRadius: 'var(--radius-sm)',
        fontSize: 12.5,
        fontWeight: 600,
        cursor: 'pointer',
        background: pd.method === o.value ? 'var(--color-white)' : 'transparent',
        color: pd.method === o.value ? 'var(--text-primary)' : 'var(--text-secondary)',
        boxShadow: pd.method === o.value ? 'var(--shadow-sm)' : 'none',
        transition: 'background var(--duration-fast) var(--ease-standard)'
      }
    }, o.label))), pd.method === 'manual' && /*#__PURE__*/React.createElement(Input, {
      label: "Manual base price",
      placeholder: "Example: 4,500,000",
      value: pd.manualBase,
      onChange: e => setPropField(l.name, 'manualBase', e.target.value)
    }), pd.method === 'median' && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        marginBottom: 6,
        position: 'relative'
      }
    }, /*#__PURE__*/React.createElement("span", {
      style: {
        fontSize: 12,
        fontWeight: 600,
        color: 'var(--text-secondary)'
      }
    }, "Market positioning factor"), /*#__PURE__*/React.createElement("img", {
      src: `https://unpkg.com/lucide-static@latest/icons/${posInfoOpen ? 'x' : 'info'}.svg`,
      onClick: () => setPosInfoOpen(o => !o),
      style: {
        width: 13,
        height: 13,
        opacity: 0.45,
        cursor: 'pointer'
      }
    }), posInfoOpen && /*#__PURE__*/React.createElement("div", {
      style: {
        position: 'absolute',
        top: 'calc(100% + 8px)',
        left: 0,
        zIndex: 10,
        width: 260,
        background: 'var(--color-white)',
        color: 'var(--text-secondary)',
        border: '1px solid var(--border-default)',
        fontSize: 12,
        lineHeight: 1.5,
        padding: '10px 12px',
        borderRadius: 'var(--radius-md)',
        boxShadow: 'var(--shadow-lg)'
      }
    }, "Positioning of this property's price relative to the market median.", /*#__PURE__*/React.createElement("br", null), "Example:", /*#__PURE__*/React.createElement("br", null), "1.1 = 10% above market", /*#__PURE__*/React.createElement("br", null), "0.9 = 10% below market")), /*#__PURE__*/React.createElement(Input, {
      value: pd.positioning,
      onChange: e => setPropField(l.name, 'positioning', e.target.value)
    })), /*#__PURE__*/React.createElement(InputWithSelectField, {
      label: "Minimum competitor count",
      value: pd.minComp,
      onChange: v => setPropField(l.name, 'minComp', v),
      options: [{
        label: 'Global: ' + globalSettings.minComp,
        value: '',
        linked: true
      }]
    })))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 14
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700,
        fontSize: 13,
        color: 'var(--text-primary)'
      }
    }, "Discounts by days left until stay"), /*#__PURE__*/React.createElement(Switch, {
      checked: pd.useUrgency !== 'off',
      onChange: v => setPropField(l.name, 'useUrgency', v ? 'on' : 'off')
    })), pd.useUrgency !== 'off' && /*#__PURE__*/React.createElement(UrgencyRulesEditor, {
      rules: pd.rules,
      setRules: u => setPropRules(l.name, u)
    })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
      style: {
        fontWeight: 700,
        fontSize: 13,
        color: 'var(--text-primary)',
        marginBottom: 12
      }
    }, "Bounds and rounding"), /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'flex',
        flexDirection: 'column',
        gap: 12
      }
    }, /*#__PURE__*/React.createElement("div", {
      style: {
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: 12
      }
    }, /*#__PURE__*/React.createElement(InputWithSelectField, {
      label: "Minimum price",
      value: pd.minIDR,
      onChange: v => setPropField(l.name, 'minIDR', v),
      options: [{
        label: 'Global: ' + globalSettings.minIDR,
        value: '',
        linked: true
      }]
    }), /*#__PURE__*/React.createElement(InputWithSelectField, {
      label: "Maximum price",
      value: pd.maxIDR,
      onChange: v => setPropField(l.name, 'maxIDR', v),
      options: [{
        label: 'Global: ' + globalSettings.maxIDR,
        value: '',
        linked: true
      }]
    })), /*#__PURE__*/React.createElement(InputWithSelectField, {
      label: "Round to nearest",
      value: pd.step,
      onChange: v => setPropField(l.name, 'step', v),
      options: [{
        label: 'Global: ' + globalSettings.step,
        value: '',
        linked: true
      }]
    })))), /*#__PURE__*/React.createElement("div", {
      style: {
        padding: '16px 28px',
        borderTop: '1px solid var(--border-default)',
        display: 'flex',
        gap: 10
      }
    }, /*#__PURE__*/React.createElement(Button, {
      variant: "accent",
      size: "sm",
      style: {
        width: '100%'
      },
      onClick: () => saveProperty(l.name)
    }, "Save"))));
  })(), document.body)));
}
window.Pricing = Pricing;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/host-dashboard/Pricing.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-site/PropertyDetail.jsx
try { (() => {
const {
  Button,
  Tag,
  Badge,
  IconButton
} = window.NicerHomesDesignSystem_ea7f10;
function Header() {
  return /*#__PURE__*/React.createElement("header", {
    style: {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '20px 48px',
      borderBottom: '1px solid var(--border-default)'
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo/nicer-wordmark.png",
    style: {
      height: 22
    }
  }), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: 'flex',
      gap: 32,
      fontFamily: 'var(--font-sans)',
      fontSize: 14,
      color: 'var(--text-secondary)'
    }
  }, /*#__PURE__*/React.createElement("span", null, "Stay"), /*#__PURE__*/React.createElement("span", null, "Host with us"), /*#__PURE__*/React.createElement("span", null, "Journal")), /*#__PURE__*/React.createElement(Button, {
    variant: "secondary",
    size: "sm"
  }, "Enquire"));
}
function Gallery() {
  const cells = [{
    big: true,
    c: 'var(--color-accent-300)'
  }, {
    c: 'var(--color-mist)'
  }, {
    c: 'var(--color-ink-200)'
  }, {
    c: 'var(--color-accent-500)'
  }, {
    c: 'var(--color-mist)'
  }];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '2fr 1fr 1fr',
      gridTemplateRows: '1fr 1fr',
      gap: 6,
      height: 420,
      padding: '0 48px',
      marginTop: 24
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      gridRow: '1 / 3',
      background: cells[0].c,
      borderRadius: 'var(--radius-lg)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      background: cells[1].c,
      borderRadius: 'var(--radius-lg)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      background: cells[2].c,
      borderRadius: 'var(--radius-lg)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      background: cells[3].c,
      borderRadius: 'var(--radius-lg)'
    }
  }), /*#__PURE__*/React.createElement("div", {
    style: {
      background: cells[4].c,
      borderRadius: 'var(--radius-lg)'
    }
  }));
}
function PropertyDetail() {
  const amenities = ['Private pool', 'Ocean view', 'Full staff', 'Rice-field access', 'Open-air living', 'Chef on request'];
  return /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-sans)',
      background: 'var(--surface-page)',
      minHeight: '100vh',
      position: 'relative'
    }
  }, /*#__PURE__*/React.createElement("div", {
    className: "glow-blob",
    style: {
      width: 480,
      height: 480,
      background: 'var(--color-accent-300)',
      top: -160,
      right: -120,
      opacity: 0.4
    }
  }), /*#__PURE__*/React.createElement(Header, null), /*#__PURE__*/React.createElement("div", {
    style: {
      padding: '32px 48px 0',
      position: 'relative',
      zIndex: 1
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'flex-start'
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-sans)',
      fontSize: 12,
      letterSpacing: 'var(--tracking-wide)',
      textTransform: 'uppercase',
      color: 'var(--text-secondary)',
      marginBottom: 8
    }
  }, "Uluwatu, Bali"), /*#__PURE__*/React.createElement("h1", {
    style: {
      fontFamily: 'var(--font-display)',
      fontWeight: 400,
      fontSize: 'var(--text-4xl)',
      margin: 0,
      color: 'var(--text-primary)',
      letterSpacing: 'var(--tracking-tight)'
    }
  }, "Villa Kayu")), /*#__PURE__*/React.createElement("div", {
    style: {
      textAlign: 'right'
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      fontFamily: 'var(--font-mono)',
      fontSize: 'var(--text-2xl)',
      color: 'var(--text-primary)'
    }
  }, "Rp 4,850,000"), /*#__PURE__*/React.createElement("div", {
    style: {
      fontSize: 13,
      color: 'var(--text-secondary)'
    }
  }, "per night")))), /*#__PURE__*/React.createElement(Gallery, null), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'grid',
      gridTemplateColumns: '1fr 340px',
      gap: 48,
      padding: '40px 48px 80px',
      maxWidth: 1200,
      position: 'relative',
      zIndex: 1
    }
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
    style: {
      fontSize: 'var(--text-lg)',
      fontWeight: 400,
      lineHeight: 'var(--leading-relaxed)',
      color: 'var(--text-primary)',
      fontFamily: 'var(--font-display)',
      maxWidth: 640
    }
  }, "A four-bedroom home set above the rice terraces, ten minutes from Uluwatu's reef breaks. Designed for slow mornings and long dinners, with a resident team looking after every detail."), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      flexWrap: 'wrap',
      gap: 8,
      marginTop: 24
    }
  }, amenities.map(a => /*#__PURE__*/React.createElement(Tag, {
    key: a
  }, a)))), /*#__PURE__*/React.createElement("div", {
    className: "glass",
    style: {
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--space-6)',
      height: 'fit-content',
      position: 'sticky',
      top: 24,
      boxShadow: 'var(--shadow-lg)'
    }
  }, /*#__PURE__*/React.createElement(Badge, {
    tone: "accent"
  }, "3 nights minimum"), /*#__PURE__*/React.createElement("div", {
    style: {
      marginTop: 16,
      display: 'flex',
      flexDirection: 'column',
      gap: 12
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: 14,
      color: 'var(--text-secondary)'
    }
  }, /*#__PURE__*/React.createElement("span", null, "Check-in"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-primary)'
    }
  }, "14:00")), /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'flex',
      justifyContent: 'space-between',
      fontSize: 14,
      color: 'var(--text-secondary)'
    }
  }, /*#__PURE__*/React.createElement("span", null, "Check-out"), /*#__PURE__*/React.createElement("span", {
    style: {
      color: 'var(--text-primary)'
    }
  }, "11:00"))), /*#__PURE__*/React.createElement(Button, {
    variant: "accent",
    size: "lg",
    style: {
      width: '100%',
      marginTop: 28
    }
  }, "Check availability"))));
}
window.PropertyDetail = PropertyDetail;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-site/PropertyDetail.jsx", error: String((e && e.message) || e) }); }

__ds_ns.Badge = __ds_scope.Badge;

__ds_ns.Button = __ds_scope.Button;

__ds_ns.Card = __ds_scope.Card;

__ds_ns.IconButton = __ds_scope.IconButton;

__ds_ns.Tag = __ds_scope.Tag;

__ds_ns.Dialog = __ds_scope.Dialog;

__ds_ns.Toast = __ds_scope.Toast;

__ds_ns.Tooltip = __ds_scope.Tooltip;

__ds_ns.Checkbox = __ds_scope.Checkbox;

__ds_ns.Input = __ds_scope.Input;

__ds_ns.InputWithSelectField = __ds_scope.InputWithSelectField;

__ds_ns.LinkedValue = __ds_scope.LinkedValue;

__ds_ns.Radio = __ds_scope.Radio;

__ds_ns.Select = __ds_scope.Select;

__ds_ns.Switch = __ds_scope.Switch;

__ds_ns.Tabs = __ds_scope.Tabs;

})();
