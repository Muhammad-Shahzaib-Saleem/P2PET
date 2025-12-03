import React, { useState, useEffect } from "react";
import { Search } from "lucide-react";

import "./SearchBar.css";

/**
 * Props:
 * - onSearch: (query) => void
 * - onActiveChange: (isActive) => void   // optional, called when input is opened/closed
 */
const SearchBar = ({ onSearch = () => {}, onActiveChange = () => {} }) => {
  const [showInput, setShowInput] = useState(false);
  const [query, setQuery] = useState("");

  // notify parent when showInput changes
  useEffect(() => {
    onActiveChange(Boolean(showInput));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showInput]);

  const toggleSearch = () => {
    // toggle open/close
    setShowInput((prev) => {
      const next = !prev;
      if (!next) {
        // closing: reset query and inform parent (onSearch(""))
        setQuery("");
        onSearch("");
      }
      return next;
    });
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    onSearch(value);
  };

  return (
    <div className="searchbar-container">
      <button
        className="search-icon-btn"
        onClick={toggleSearch}
        aria-label={showInput ? "Close search" : "Open search"}
      >
        <Search size={18} />
      </button>

      {showInput && (
        <input
          autoFocus
          type="text"
          className="search-input"
          placeholder="Search meters..."
          value={query}
          onChange={handleInputChange}
        />
      )}
    </div>
  );
};

export default SearchBar;


// import React, { useState } from "react";
// import { Search } from "lucide-react";

// import "./SearchBar.css";

// const SearchBar = ({ onSearch }) => {
//   const [showInput, setShowInput] = useState(false);
//   const [query, setQuery] = useState("");

//   const toggleSearch = () => {
//     setShowInput((prev) => !prev);
//     if (showInput) {
//       setQuery("");
//       onSearch(""); // reset when closed
//     }
//   };

//   const handleInputChange = (e) => {
//     const value = e.target.value;
//     setQuery(value);
//     onSearch(value);
//   };

//   return (
//     <div className="searchbar-container">
//       <button className="search-icon-btn" onClick={toggleSearch}>
//         <Search size={20} />
//       </button>
//       {showInput && (
//         <input
//           type="text"
//           className="search-input"
//           placeholder="Search meters..."
//           value={query}
//           onChange={handleInputChange}
//         />
//       )}
//     </div>
//   );
// };

// export default SearchBar;
