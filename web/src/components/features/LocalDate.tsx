type Props = {
  isoString?: string | null;
  locale?: string;
  withSeconds?: boolean;
};

const LocalDate: React.FC<Props> = ({
  isoString,
  locale = "ja-JP",
  withSeconds = false,
}) => {
  if (!isoString) return null;

  const date = new Date(isoString);
  if (isNaN(date.getTime())) return null;

  const options: Intl.DateTimeFormatOptions = {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    ...(withSeconds && { second: "2-digit" }),
    hour12: false,
  };

  const formatted = new Intl.DateTimeFormat(locale, options).format(date);

  return <>{formatted}</>;
};

export default LocalDate;
