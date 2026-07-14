import { useState, type InputHTMLAttributes } from "react";

type TextFieldProps = InputHTMLAttributes<HTMLInputElement>;

/** 포커스(클릭)하는 즉시 placeholder를 숨기는 input. 값을 입력하지 않고 포커스를 벗어나면 다시 보여준다. */
export function TextField({ placeholder, onFocus, onBlur, ...rest }: TextFieldProps) {
  const [focused, setFocused] = useState(false);

  return (
    <input
      {...rest}
      placeholder={focused ? "" : placeholder}
      onFocus={(e) => {
        setFocused(true);
        onFocus?.(e);
      }}
      onBlur={(e) => {
        setFocused(false);
        onBlur?.(e);
      }}
    />
  );
}
