import { createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';
import { Link } from '@tanstack/react-router';
import { Button } from "../components/ui/button";
import { createServerFn } from '@tanstack/start';

export const Route = createFileRoute('/enterKey')({
  component: EnterKeyComponent,
});

export const updateApiKey = createServerFn({ method: 'POST' })
  .validator((input: { api_key: string }) => {
    const trimmedKey = input.api_key.trim();

    if (!trimmedKey) {
      throw new Error('API key is required and cannot be empty.');
    }

    if (trimmedKey.length < 30) {
      throw new Error('API key must be at least 30 characters long.');
    }

    return { api_key: trimmedKey };
  })
  .handler(async ({ data }) => {
    const response = await fetch("http://localhost:8000/api/input/key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Failed to save API key');
    }
    const result = await response.json();
    return result;
  });

function EnterKeyComponent() {
  const [apiKey, setApiKey] = useState('');
  const [message, setMessage] = useState('');
  const [isError, setIsError] = useState(false);

  const handleSubmit = async () => {
    try {
      const data = await updateApiKey({ data: { api_key: apiKey }});
      setMessage(data.message);
      setApiKey('')
      setIsError(false);
    } catch (error: any) {
      setMessage('Error: ' + error.message);
      setIsError(true);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-screen space-y-6">
      <h3 className="text-center text-2xl font-semibold">
        Enter your API Key
      </h3>
      <input
        type="password"
        placeholder="API Key"
        value={apiKey}
        onChange={(e) => setApiKey(e.target.value)}
        className="border-2 border-gray-500 focus:border-blue-300 focus:ring-2 focus:ring-blue-500 rounded-lg p-3 text-lg bg-zinc-700 text-white placeholder-gray-400 transition duration-200 ease-in-out"
        />
      <Button onClick={handleSubmit} variant="default" size="lg">
        Submit API Key
      </Button>
      {message &&  <p className={`text-sm ${isError ? 'text-red-500' : 'text-green-500'}`}>
          {message}
        </p>}
      <Link to="/">
        <Button variant="default" size="lg">Go Back</Button>
      </Link>
    </div>
  );
}
