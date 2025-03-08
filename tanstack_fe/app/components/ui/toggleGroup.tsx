import { ToggleGroup } from "radix-ui";
import { FileType } from "~/types";

interface ToggleGroupBaseProps {
    items: { value: string; label: string }[],
    value: string,
    onValueChange: (value: FileType) => void,
    defaultValue?: string,
    containerClassName?: string,
    itemClassName?: string
}

const ToggleGroupBase = ({
  items = [],
  value,
  onValueChange,
  defaultValue = '',
  containerClassName = "",
  itemClassName = "",
}: ToggleGroupBaseProps) => (
    <ToggleGroup.Root
    className={`inline-flex space-x-px rounded bg-zinc-700 shadow-[0_2px_10px] shadow-blackA4 ${containerClassName}`}
    type="single"
    value={value}
    defaultValue={defaultValue}
    onValueChange={onValueChange}
    aria-label="File type selection"
  >
    {items.map((item) => (
      <ToggleGroup.Item
        key={item.value}
        className={`flex h-[25px] w-[50px] items-center justify-center bg-zinc-900 text-gray-100 text-xs font-bold leading-4 
            first:rounded-l last:rounded-r hover:bg-zinc-800 focus:z-10 focus:shadow-[0_0_0_2px] focus:shadow-black focus:outline-none 
            data-[state=on]:bg-zinc-200 data-[state=on]:text-zinc-800 border border-gray-400 ${itemClassName}`}
        value={item.value}
        aria-label={item.label}
      >
        {item.label}
      </ToggleGroup.Item>
    ))}
  </ToggleGroup.Root>
);

export default ToggleGroupBase;
